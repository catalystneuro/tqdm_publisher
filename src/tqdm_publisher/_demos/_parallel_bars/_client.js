import { WebSocketManager } from '../utils/WebSocketManager.js';
import { barContainer, createProgressBar } from '../utils/elements.js';

const bars = {} // Track progress bars
const requests = {} // Track request containers

function getRequestContainer(request_id) {
    const existing = requests[request_id]
    if (existing) return existing;

    // Create a new container for the progress bar
    const container = document.createElement('div');
    container.id = request_id;
    container.classList.add('request-container');
    const h2 = document.createElement('h2');
    h2.innerText = `Request ID: ${request_id}`;
    container.append(h2);
    document.body.append(container);
    requests[request_id] = container;
    return container;
}

// Create and/or render a progress bar
const getBar = (request_id, id) => {
    
    if (bars[id]) return bars[id];

    const container = getRequestContainer(request_id);
    const bar = createProgressBar(container);

    return bars[id] = bar;
    
}

// Update the specified progress bar when a message is received from the server
const onProgressUpdate = (event) => {
    const { request_id, id, format_dict } = JSON.parse(event.data);
    const bar = getBar(request_id, id);
    bar.style.width = 100 * (format_dict.n / format_dict.total) + '%';
}

// Create a new WebSocket client
const client = new WebSocketManager({ onmessage: onProgressUpdate });

// Declare that the HTML Button should create a new progress bar when clicked
const button = document.querySelector('button');
button.addEventListener('click', () => {
    const request_id = Math.random().toString(36).substring(7); // Create a unique ID for the progress bar
    client.socket.send(JSON.stringify({ command: 'start', request_id })); // Send a message to the server to start the progress bar
})
