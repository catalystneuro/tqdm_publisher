import { EventSourceManager } from '../utils/EventSourceManager.js';
import { getBar } from '../utils/elements.js';


// Update the specified progress bar when a message is received from the server
const onProgressUpdate = (event) => {
    const { request_id, progress_bar_id, format_dict } = JSON.parse(event.data);
    const { update } = getBar(request_id, progress_bar_id);
    update(format_dict, { request_id, progress_bar_id });
}

// Create a new message client
const client = new EventSourceManager({ onmessage: onProgressUpdate });

// Declare that the HTML Button should create a new progress bar when clicked
const button = document.querySelector('button');
button.addEventListener('click', async () => {
    const request_id = Math.random().toString(36).substring(7); // Create a unique ID for the progress bar
    getBar(request_id, request_id); // Create a bar specifically for this request
    await client.send({ command: 'start', request_id }).catch(() => {}); // Send a message to the server to start the progress bar
})
