#ifndef thermistor_h
#define thermistor_h

float adc_to_vout(int adc);
float steinhart_hart(int adc);
float dac_to_fahrenheit(int adc);
float dac_to_celsius(int adc);

#endif
