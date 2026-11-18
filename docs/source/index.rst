Owner's Manual
==============
Welcome and we hope you enjoy your Growbies scale!

Growbies scales are built for growing.

If reading this manaul online, please be sure the version matches that found on your scale at
`Configuration->Info->FW Version`.

.. _quick-start:

Quick Start
-----------
1. Place the scale under a containerized plant. That is, any plant growing in a pot, bag, etc.
2. Zero the scale at a soil moisture weight of interest.
3. Irrigate back to zero, returning the amount of water that has evaporated and transpired.

Zero the scale via `Tare [A,B,C] -> Tare -> Zero`. Try not to disturb the scale while zeroing.

You, as the grower, know what soil moisture the plant needs. Setting the zero point of the scale
helps maintain the desired soil moisture. This is accomplished via

1. The zero point providing a quantitative reference to the grower
2. The builtin display feedback improving hand watering consistency and accuracy
3. Soil moisture telemetry as feedback in natural and automated irrigation contexts.

Design Features
---------------
Growbies scales are thermally calibrated. This allows accurate readings with varying temperature.
Each load cell is independently thermally calibrated and measured.

These scales implement a summing load cell topology that allows for thermal isolation from the
frame. Each load cell is effectively an independent scale. This improves accuracy in rugged
environments.

The tripod footprint of the circular scales are inherently stable, in that, all three points will
touch in varied terrain without rocking.

For indoor/outdoor use. Water spray and dust resistant.

.. image:: _static/images/top_annotated.png
.. image:: _static/images/bottom_annotated.png

Built-in Display
----------------
The built-in display has three buttons; `up`, `down` and `select`. The menu is organized similar to file
system tree. Select descends into the tree, returning to the top level when selecting past the bottom.

The `+` character indicates there is more beneath the currently selected menu item that can be accessed
by pressing `select`. The `-` character indicates that the associated menu item is already accessed. The
`>` character means that the leaf, or the bottom, of the tree has been reached. Pressing `select` again
will return to the top of the tree.

Map
~~~
.. code-block:: text

    ├── Tare A-C
    │   ├── Tare
    │   │   ├── Zero
    │   │   └── Cancel
    │   │
    │   ├── Units
    │   │   ├── g: grams
    │   │   ├── kg: kilograms
    │   │   ├── oz: ounces
    │   │   └── lb: pounds
    │   │
    │   ├── Error
    │   │   └── <error code>: <error description>
    │   │
    │   └── Load Cell 1-N
    │       ├── <mass value> <units>
    │       └── <error code>: <error description>
    │
    ├── Temperature
    │   ├── Units
    │   │   ├── C: Celsius
    │   │   └── F: Fahrenheit
    │   │
    │   ├── Error
    │   │   └── <error code>: <error description>
    │   │
    │   └── Load Cell 1-N
    │       ├── <temperature value> <units>
    │       └── <error code>: <error description>
    │
    └── Configuration
        │
        ├── Power
        │   ├── Sleep
        │   │   ├── True
        │   │   └── False
        │   │
        │   ├── Sleep TO (s)
        │   │   └── 0, 1, 2, 3, 5, 8, 15, 20, 30, 60, 90, 120, 240, 360, 480, 600, 1200
        │   │
        │   └── Battery
        │       ├── charging
        │       └── discharging
        │
        ├── Display
        │   ├── Flip
        │   │   ├── True
        │   │   └── False
        │   │
        │   └── Contrast
        │       └── 0-255
        │
        └── Info
            ├── Model No
            ├── FW Version
            ├── Source Hash
            ├── Mfg Date
            └── Serial No.

Definitions
~~~~~~~~~~~
- `Tare A-C`: These are values that are subtracted from the absolute mass. These tare values map to
  points of interest in the real world. Such as, "the irrigate to" weight, the "empty scale" weight,
  they can be mapped to specific plants, the "too moist" and "too dry" points. The tare values can be
  zeroed to any point of interest by the grower.
- `Tare A-C -> Tare -> Zero`: Set the zero point of the associated tare.
- `Tare A-C -> Tare -> Cancel`: Cancel (do nothing) setting the zero point of the associated tare.
- `Tare A-C -> Units`: Select the units for displaying mass.
- `Tare A-C -> Error`: The current error state of the aggregate mass.
- `Tare A-C -> Load Cell 1-N`: The per load cell mass as well as any error.

- `Temperature`: The aggregate temperature of the scale. It is an average of the three load
  cell temperature measurements.
- `Temperature -> Units`: Select the units for temperature display.
- `Temperature -> Error`: The current error state of the aggregate temperature.
- `Temperature -> Load cell 1-N`: The per load cell temperature and any associated error.

- `Configuration`: System configuration and information menu.
- `Configuration -> Power -> Sleep`: Selecting `True` will put the device into a low power sleep mode.
  Selecting `False` will cancel the request for sleep.
- `Configuration -> Power -> Sleep TO (s)`: The sleep timeout in seconds. This is how many seconds the
  display will remain active before going to sleep. Button presses resets the timer. Jostling the scale
  beyond a 50 gram threshold will keep the scale awake.
- `Configuration -> Power -> Battery`: The charging state of the battery, either "charging" if the USB
  cable is plugged in or "discharging" when running on the battery alone.
- `Configuration -> Display`: Display specific configuration menu
- `Configuration -> Display -> Flip`: Flip the display over for left/right hand use. THe built-in
  display can be physically flipped over to match.
- `Configuration -> Display -> Contrast`: Turn the contrast up/down for the display. A lower value
  corresponds to a lower (dimmer) contrast) and vice versa. The range of values is [0,255], inclusively.
- `Configuration -> Info`: Information (read-only) menu
- `Configuration -> info -> Model No.`: The model number.
- `Configuration -> info -> FW Version`: The firmware version. Use this value to match the owner's
  manual version to ensure the docs match the firmware.
- `Configuration -> info -> Source Hash`: The commit hash of the firmware.
- `Configuration -> info -> Mfg Date`: The date of manufacture.
- `Configuration -> info -> Serial No.`: The serial number of the device.

Use Case Scenarios
------------------
Growbies scales are not intended to be a complete growing solution. Rather, they are intended to aid
the grower in their efforts. Here are some scenarios in which Growbies scales are useful. This is not
an exhaustive list.

Soil Moisture Tracking
~~~~~~~~~~~~~~~~~~~~~~
As mentioned in the :ref:`Quick Start <quick-start>` section, Growbies scales provide a means to track
soil moisture of a grow via gravimetric means.

Place a containerized plant on the scale. Water it as desired. Zero the scale. Now the zero point is a
reference to the grower on the soil moisture state. Over time, the scale will read more and more
negative. THis is the amount of water that has left the grow via evaporation and transpiration.

At the time of watering, the scale provides real-time feedback to the grower, allowing more accurate
irrigation. Additionally, because the mass is tracked over time, the grower can irrigate back to the
zero point that was set previously.

With this, irrigation stays tied to a quantitative soil moisture reference, represented by the zero
point of one of the provided Tare A, B or C.

The zero point can be set relative to the
:ref:`maximum soil moisture saturation <soil-moisture-saturation-discovery>`. Some plants prefer
consistent irrigation closer to the saturation point, while others prefer a drier growing medium.

.. _soil-moisture-saturation-discovery:

Soil Moisture Saturation Discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The maximum amount of moisture that the soil can hold can be determined with the help of this scale.
Irrigate the plan until water begins to drip from the bottom of the container. Once the water has
stopped leaking from the bottom, read the mass from the scale. This is the weight of the grow when the
soil is saturated.

Note, the maximum soil moisture can vary depending on the history of irrigation. e.g. dry soil is
hydrophobic, whereas soil that has been kept relatively moist over time will retain more moisture.

Again, this scale can help the grower understand the relationship between the historical moisture
content and the maximum soil moisture content.

General Purpose
~~~~~~~~~~~~~~~
- measure harvests
- weigh out dry soil when potting
- weigh homogonous growing containers to ensure consistency across the batch. For example, if growing
  pepper plants, each in a container, each can be placed on the scale and irrigate for irrigation
  consistency across all of them

Gateway
-------
Remove the dust cap and connect the scale to a Growbies gateway via the provided USB-A to USB-C cable.
This provides programmatic access to the device. For more detailed information, including
information regarding valuable insights provided by time tracking the weight of a grow, please see
`Gateway Documentation <../gateway/index.html>`_ .

