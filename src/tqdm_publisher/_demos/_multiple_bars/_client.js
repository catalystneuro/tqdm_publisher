import { WebSocketManager } from '../utils/WebSocketManager.js';
import { createProgressBar } from '../utils/elements.js';

const bars = {} // Track progress bars

// Update the specified progress bar when a message is received from the server
const onProgressUpdate = (event) => {
    const { request_id, format_dict } = JSON.parse(event.data);
    const { update } = bars[request_id];
    update(format_dict);

}

// Create a new WebSocket client
const client = new WebSocketManager({ onmessage: onProgressUpdate });

// Declare that the HTML Button should create a new progress bar when clicked
const button = document.querySelector('button');
button.addEventListener('click', () => {
    const request_id = Math.random().toString(36).substring(7); // Create a unique ID for the progress bar
    bars[request_id] = createProgressBar(); // Create and render a progress bar
    client.socket.send(JSON.stringify({ command: 'start', request_id })); // Send a message to the server to start the progress bar
})
