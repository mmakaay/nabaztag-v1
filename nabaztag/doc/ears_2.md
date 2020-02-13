## Nabaztag ears

The ears on the Nabaztag can be moved either manually or by a motor.
To know how far the ears have moved, two encoder wheels are available in the
hardware of the bunny. Each ear has its own, independent encoder.

The encoder wheel is a basic gear, combined with an IR LED/sensor. Each time an
encoder gear notch comes in front of the IR sensor, the encoder value is
incremented. There is only a single sensor in this encoder, which means that
the encoder cannot report the direction in which the ear is turning. It can
only report the number of notches that it has seen.

The encoder wheel has 20 notch positions, however 3 consecutive notches are
missing. These form a gap that we can use for homing the ear.

## Terminology

From now on, I will talk about:

  * encoder value [0 - 255]
  * ear position  [0  - 19]
  * real notch    [0  - 16]
  * virtual notch [17 - 19]

## Related bytecode opcodes

We don't have much to work with in the ear rotation department. There are
only two opcodes (`MOTOR` and `MOTORGET`) to work with.

In these motor-related opcodes, the motor register holds either 0 (motor for
the left ear) or 1 (motor for the right ear).

Starting and stopping a motor can be done using the `MOTOR <M> <D>` opcode.
This will apply the direction `D` to motor `M`. The direction is one of:

  * 0: stop the motor
  * 1: start motor
  * 2: start motor in reverse

The encoder value for an ear can be retrieved using the `MOTORGET <A> <M>`
opcode. This will store the encoder value for the requested motor `M` in the
assembly register `A`. The encoder value will be in the range [0 - 255].
When the encoder is at value 255, the next value will be 0.

## Logical layout

The layout below is a logical layout for the ears, constructed in such way
that after homing the ear (see below) encoder notch number 0 is ligned up with
ear position number 0. This is not necessarily how things are constructed
mechanically, but it is the most useful mental model for coding purposes.

The position of the ear after homing has been determined by means of a
few experiments.

```
     Forward                            EAR
       .               03   02   01     *
     .`           04                  00
    /                               LED          *) The ear is aligned with
   |          05         .  .  .   v      19        encoder notch nr. 00.
   v                  16          00                After homing, the ear is
            06      15           /  01      18      therefore at position 0.
                   14        sensor  02
   Front   07  --- 13        o       03 ---  17    Back
                   12                04
            08      11              05      16
   ^                  10          06
   |          09     /   09 08 07   \     15
    \               /        |       \
     `.           10         |        14
       `               11   12   13
     Backward
```

The inner cicle represents the rotating encoder wheel with the three missing
notches. This is the wheel that is rotated when the ears are moved (by motor
or manually).

The outer circle represents the directions that the ear can be moved to by the
ear control code in the assembly library. This circle does not rotate when
moving the ears, the directions are static.

Here's what the layout would look like after moving the ear straight forward
(i.e. position 7):

```
                  03   02   01
             04                  00
                              LED
         05         04 05 06  /      19
                 03          07
       06      02           /  08      18
              01        sensor  09
EAR * 07  --- 00        o       10 ---  17
              .                 11
       08      .               12      16
                 .           13
         09     /   16 15 14   \     15
               /        |       \
             10         |        14
                  11   12   13
```

This clearly displays the rationale behind the logical layout. To move
the ear to position 7, the encoder wheel must be moved to position 7
as well.

## Strategy for homing an ear

The basic strategy is fairly simple: Start the motor and wait for the encoder
to pass the gap. The gap is detected by the fact that no notch is seen for at
least twice the time of a regular encoder value change.

___Considerations:__

An ear does a full rotation in about 6 seconds (as seen by rough manual
measurements). This means that one position takes about 6000/20 = 300 ms for
rotation. This value is used as the default value in the homing algorithm.
The real time might vary though. Therefore, in the algorithm, we keep track
of the lowest encoder value change time that we see. Later on, we can use
the value that we found this way in the ear moment strategy.

An prerequisite here, is that the ear can rotate freely. When the motor for
an ear is broken or when the ear is blocked for some reason, the strategy
will (possibly incorrectly) decide that we must be at the gap, since no new
notches will be detected. After this, it will try to move forward to the first
upcoming encoder wheel notch. That notch might never arrive. To not block the
bunny's operation, we have to implement a timeout in the homing strategy.

__"Code"__

Everything combined, in pseudo-code the homing algorithm for an ear looks
like the following. There are some RAM(..) references in there. These are
references to state information that will be stored in the device's RAM.
These RAM fields will be explain furter down in the document in detail.

```
function home_ear():
    $time_per_position = 300
    $timeout_in_ms = 20000

    RAM(encoder state) = 0 # not in sync

    start the motor in forward mode

    $t1 = current time in ms
    $e1 = current encoder value

    @wait_for_gap
        # Retrieve the new position and time.
        $e2 = current encoder value
        $t2 = current time in ms

        # Compute the difference with the previous values.
        $t_diff = $t2 - $t1
        $e_diff = $e2 - $e1

        # Check if we moved to a new encoder value.
        if $e_diff > 0:
            # Check if the time per position is lower than the currently used
            # time per position. If yes, then use the new value.
            $measured_time_per_position = $t_diff // $e_diff
            if $measured_time_per_position < $time_per_position:
                $time_per_position = $measured_time_per_position

            # Set new start values and and start waiting for the gap again.
            $t1 = current time in ms
            $e1 = $e2
            goto @wait_for_gap

        # Check if we are at the gap.
        if $t_diff > (2 * $time_per_position):
            goto @wait_for_notch_after_gap

        goto @wait_for_gap

    @wait_for_notch_after_gap
        # Retrieve the new position and time.
        $e2 = current encoder value
        $t2 = current time in ms

        # When the encoder value changed, we passed the gap.
        if $e1 <> $e2:
            RAM(encoder state) = 1 # in sync
            goto @done

        # On timeout, stop looking for the end of the gap.
        if ($t2 - $t1) > $timeout_in_ms:
            goto @done

        goto @wait_for_notch_after_gap

    @done
        stop the motor
        RAM(last known encoder value) = $e2
        RAM(last known position) = 0
        RAM(time per position) = $time_per_position
```

## Strategy for moving an ear

An ear can be moved in two ways: using a motor or manually. The strategy
devised here has to take into account that we want to be able to detect
manual ear movement. Unfortunately, there is not something like a hardware
interrupt for this, so we'll have to handle everything ourselves.
To make things easier for users of the core library, a software interrupt
will be implemented to notify about manual ear movement.

When moving an ear using a motor, the following input parameters apply:

  * The ear to move (left or right)
  * The direction in which to move the ear (forward or backward)
  * The position to which to move the ear (0 -19)

Because there is almost no information available for an ear (there's only the
encoder value), we'll have to keep track of the state ourselves in the
bunny's RAM. The fields that we will use for this are:

 * The state of the encoder (0: not in sync, 1: in sync)
 * The time (in msec) between two positions (set by homing)
 * The last known ear position (0 - 19, initialized to 0 by homing)
 * The last known encoder value (initialized by homing)
 * A 16-bit value repressenting the time (in msec) of the last encoder change
 * The state of the motor (0: stopped, 1: forward, 2: reverse)
 * The target ear position (0 - 19)

So 8 bytes are used to store the ear state. For both ears, 16 bytes are used.
Some fields could be combined using bitwise operations, but as long as we
don't run into memory exhaustion issues, using 16 bytes is okay; there are
256 - 16 = 240 RAM bytes left for the system stack and other RAM data.

The core concept for the strategy is an endless loop that repeatedly inspects
the encoder status for the ear.

The exact implementation of this loop can be ignored here. It might be a
loop as provided by the core library, or a loop that is separately written.
The thing to focus on, is the logic to apply for the encoder inspection.
This logic can be applied from any loop mechanism.

___Considerations:__

Ideally, the loop invokes the encoder inspection code at least twice during
the minimum time between encoder notches (as determined during the homing
process). We should however be prepared to handle encoder changes in case
the inspection is invoked less often.

Just like with homing, an ear might get stuck. In such case, a timeout
should apply, after which the motor is stopped and the encoder is flagged
out of sync.

__"Code"__

There are multiple functions involved in moving an ear:

  * Start ear movement
  * Stop ear movement
  * Update ear state (used within the beforementioned endless loop)

In the pseudo-code below, I don't bother about handling an input parameter
that identifies a specific ear. That is a concern for the actual
implementation.

__start__

```
function start_motor($direction, $target_position):

    # Encoder out of sync? Then we first try to home the ear.
    # If homing fails, then we won't continue.
    if RAM(encoder state) == 0:
        call home_ear()
        if RAM(encoder state) == 0:
            return

    # Motor already running in the requested direction?
    # Then we only need to update the target position.
    if RAM(motor state) == $direction:
        goto @set_target

    # Motor running in the opposite direction? Then first stop it
    # and update the motor state, before starting it in the
    # requested direction.
    if RAM(motor state) != 0:
        call stop_motor()

    start the motor in $direction
    RAM(motor state) = $direction

    @set_target
        RAM(target) = $target_position
```

__stop__

```
function stop_motor():
    stop the motor
    call update_motor_state()
```

__update__

```
$time_per_position = RAM(time per position)
$timeout_in_ms = 20000

function update_motor_state():
```

