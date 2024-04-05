import { EventSourceManager } from '../utils/EventSourceManager.js';
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
    const barContainer = document.createElement('div');
    barContainer.classList.add('bar-container');
    container.append(barContainer);
    requests[request_id] = barContainer;

    return barContainer;
}

// Create and/or render a progress bar
const getBar = (request_id, id) => {

    if (bars[id]) return bars[id];

    const container = getRequestContainer(request_id);
    const bar = createProgressBar(container);

    bar.parentElement.setAttribute('data-small', request_id !== id); // Add a small style to the progress bar if it is not the main request bar

    return bars[id] = bar;

}

// Update the specified progress bar when a message is received from the server
const onProgressUpdate = (event) => {
    const { request_id, id, format_dict } = JSON.parse(event.data);
    const bar = getBar(request_id, id);
    bar.total = format_dict.total
    bar.n = format_dict.n

    // Update summary bar
    if (format_dict.n === format_dict.total) {
        const sumBar = bars[request_id]
        if (sumBar) {
            sumBar.n++
            sumBar.style.width = 100 * (sumBar.n / sumBar.total) + '%';
        }
    }

    bar.style.width = 100 * (bar.n / bar.total) + '%';
}

// Create a new message client
const wsClient = new WebSocketManager({ onmessage: onProgressUpdate }, 3);
const client = new EventSourceManager({ onmessage: onProgressUpdate });

// Declare that the HTML Button should create a new progress bar when clicked
const button = document.querySelector('button');
button.addEventListener('click', async () => {
    const request_id = Math.random().toString(36).substring(7); // Create a unique ID for the progress bar
    getBar(request_id, request_id); // Create a bar specifically for this request
    await client.send({ command: 'start', request_id }).catch(() => {}); // Send a message to the server to start the progress bar
    wsClient.send({ command: 'start', request_id }); // Send a message to the server to start the progress bar
})
