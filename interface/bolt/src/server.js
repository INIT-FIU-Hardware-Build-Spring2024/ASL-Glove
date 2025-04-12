const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const { SerialPort } = require('serialport');
const { ReadlineParser } = require('@serialport/parser-readline');
const cors = require('cors');

const app = express();
app.use(cors());
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Set the port for your server - this can be any free port
const PORT = 3001;

// Configure with your Arduino port - you'll need to change this to match your setup
// Common ports: 'COM3' (Windows), '/dev/ttyUSB0' or '/dev/ttyACM0' (Linux), '/dev/tty.usbmodem*' (Mac)
const SERIAL_PORT = 'COM3';
const BAUD_RATE = 9600;

// Create the serial port connection
let serialPort;
try {
  serialPort = new SerialPort({ path: SERIAL_PORT, baudRate: BAUD_RATE });
  console.log(`Serial port opened: ${SERIAL_PORT}`);
} catch (err) {
  console.error('Error opening serial port:', err.message);
}

// Create a parser for the data
const parser = serialPort.pipe(new ReadlineParser({ delimiter: '\r\n' }));

// Event handler for WebSocket connections
wss.on('connection', (ws) => {
  console.log('Client connected');
  
  // Send a welcome message to the client
  ws.send(JSON.stringify({ type: 'connection', status: 'connected' }));
  
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Listen for data from the Arduino
parser.on('data', (data) => {
  console.log('Arduino data:', data);
  
  // Parse the data and broadcast to all connected clients
  try {
    // This assumes your Arduino is sending data in a format like:
    // "I:123,M:456,R:789,P:101,WORD:hello"
    // If your format is different, adjust this parsing logic
    
    // For now, just forward the raw data
    const message = {
      type: 'sensorData',
      rawData: data
    };
    
    // Send to all connected clients
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(message));
      }
    });
  } catch (error) {
    console.error('Error parsing data:', error);
  }
});

// Error handler for the serial port
serialPort.on('error', (err) => {
  console.error('Serial port error:', err.message);
});

// Start the server
server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

// Add a basic API endpoint for testing
app.get('/status', (req, res) => {
  res.json({ status: 'Server running', serialPort: SERIAL_PORT });
});