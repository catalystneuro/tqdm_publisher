import { WebSocketManager } from '../utils/WebSocketManager.js';
import { createProgressBar } from '../utils/elements.js';

const { update, progress } = createProgressBar(); // Create and render a progress bar

// Update the specified progress bar when a message is received from the server
const onProgressUpdate = (event) => {
    const { format_dict } = JSON.parse(event.data);
    const ratio = format_dict.n / format_dict.total;
    update(format_dict); // Update the progress bar with the new progress

    if (ratio === 1) button.removeAttribute('disabled'); // Enable the button when the progress bar is complete
}

// Create a new WebSocket client
const client = new WebSocketManager({ onmessage: onProgressUpdate });

// Declare that the HTML Button should create a new progress bar when clicked
const button = document.querySelector('button');
button.addEventListener('click', () => {
    button.setAttribute('disabled', true); // Disable the button to prevent multiple progress bars from being created
    progress.style.width = 0; // Reset the progress bar
    client.socket.send(JSON.stringify({ command: 'start' })); // Send a message to the server to start the progress bar
})
