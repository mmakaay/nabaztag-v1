# Ears

The ears of the Nabaztag are moved by two motors, which can be controlled
independently and which can rotate the ears both forward and backward.

Each motor has a related encoder unit, which is used to control the
positioning of the ears and to detect whether the ears have been moved manually.
Each full rotation of an ear corresponds to one full rotation of the encoder wheel.

The encoder is a 20 notch wheel, of which 3 notches are missing. The missing notches are used for homing the ears to their starting position.
An IR sensor looks at the wheel, and every time a tooth comes in front of the
sensor, the encoder value is incremented (from 0 to 255, wrapping around
back to 0).

Below's a schema of the way in which the encoder wheels are laid out,
after completing the homing operation.

The inner circle represents the hardware encoder wheel with the three missing
notches. Each number references an actual notch.

The outer circle represents the direction values as implemented in the core ear
position code.

For example, when rotating an ear forward from direction 18 to direction 0,
the ear will point straight up after the move operation. The inner wheel
will then have moved from notch 0 to notch 2.

When rotating an ear backward from direction 18 to position 15, it will
end up straight backwards. The inner wheel will have moved from notch 0
to right before notch 16. This is an interesint problem in programming
the ear movement, because between notches 0 and 16, movement has to be
performed based on timing instead of actual encoder value changes.

```
     Forward
       .               01   00   19
     .`           02         |        18
    /               \        |       /
   |          03     \   13 14 15   /     17     *) The ear is aligned with
   v                  12          16                encoder notch nr. 16
            04      11           *  xx      16
                   10                xx
   Front   05  --- 09        o       xx ---  15    Back
                   08           IR>> 00
            06      07              01      14
   ^                  06          02
   |          07     /   05 04 03   \     13
    \               /        |       \
     `.           08         |        12
       `               09   10   11
     Backward
```

Because there is only a single encoder per ear, is it not possible to tell
in which direction an ear is turning when it is moved manually. In both
directions, the encoder value is incremented. The best that can be done
here, is detecting that the ears have moved over a certain range (forward,
backward or a combination of these).

