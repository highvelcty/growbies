Velostat Pressure Sensing Investigation
=======================================

In late 2024, into early 2025, an investigation was made into the possibility of using velostat
as a means for cost effective load sensing.

The resistance of velostat changes with pressure. When sandwiched between conductive material, it
can be used as a pressure sensor.

Here is a load cell built from copper tape, washers and velostat. It is then sealed with packing
tape:

.. image:: binary/washer_sensor.jpg
    :alt: A sandwich of packing tape, copper coated washer, velostat, copper coated washer,
          packing tape.

These were glued to the bottom of a gardening cup. The purple lettuce plant was then placed into
the cup.

.. image:: binary/washer_sensor_cup.jpg
    :alt: Velostat washer sandwiches installed on the bottom of a gardening cup. A plant that
          will go into the cup is also shown.

Data was collected via Arduino.

.. image:: binary/washer_sensor_data.png

Other sensors were investigated.

.. image:: binary/sensor_misc.jpg

This one is 12 gauge copper wire, wrapped in two layers of velostat strips. The velostat layers are
wrapped in a copper strip layer. This copper velostat ring sandwich is compressed between two
regular mouth canning lids in a canning ring. The sandwich is then compressed with a disc of
particle board. There is a 220 ohm resistor in line.

Expanded form:

.. image:: binary/ring_sensor_expanded.jpg

Assembled form:

.. image:: binary/ring_sensor_assembled.jpg

The above velostate ring sensor was placed on a kitchen scale. 5 volts was applied to the following
resistor divider.

.. image:: binary/velostat_circuit.png

A photographic time lapse was taken of 1. the kitchen scale display and 2. a voltmeter displaying
Vo in the circuit above, using the above velostat ring sensor.

The data was read from the pictures via a trained
`Tesseract <https://github.com/tesseract-ocr/tesseract>`_ models.

    - `mm.traineddata <https://github.com/highvelcty/growbies/blob/main/tesseract/mm.traineddata>`_
      # For reading the multi-meter (voltmeter) display.
    - `scale.traineddata <https://github.com/highvelcty/growbies/blob/main/tesseract/scale.traineddata>`_
      # For reading the kitchen scale output

