# IoT-Lora-Project
This project is designed to communicate with a cloud broker hosted on EMQX, store temperature readings from a LoRa sensor, and plot a graph showing how the temperature varies throughout the day. Additionally, it displays a square that turns green or red based on the temperature value, in this case, indicating whether a heater is on or off.

To run the program, use your preferred Python interpreter (tested on version 3.12.6, 64-bit) and ensure the required libraries such as tkinter, pandas, and others are installed. Finally, create an EMQX account and configure the emqxsl-ca.crt file and the address in mqtt_client.py. You can also change the username and password if needed, or use the default credentials provided.
