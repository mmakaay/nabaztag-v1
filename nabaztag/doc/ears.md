# Ears

The ears of the Nabaztag are moved by two motors, which can be controlled
independently and which can rotate the ears both forward and backward.

Each motor has a related encoder unit, which is used to control the
positioning of the ears and to detect whether the ears have been moved manually.

The encoder is a 20 teeth wheel, which misses 3 of its teeth. Each full rotation
of an ear corresponds to one full rotation of the encoder wheel. Here's a schema
of the way in which the encoder wheels are laid out, using the tooth numbering
that other projects use as well:

```
                   top
           \        |       /
            \   04 03 02   /<.
             05          01    `.  encoder gap
           06             (20)   .
          07               (19)   .
 front -- 08        o      (18) -- + back
          09                17
           10              16
             11          15
            /   12 13 14   \
           /        |       \
                 bottom

```

An IR sensor looks at the wheel, and every time a tooth comes in front of the
sensor, the encoder value is incremented (from 0 to 255, wrapping around
back to 0).

Because there is only a single encoder per ear, is it not possible to tell
in which direction an ear is turning when it is moved manually. In both
directions, the encoder value is incremented. The best that can be done
here, is detecting that the ears have moved over a certain range (forward,
backward or a combination of these).


