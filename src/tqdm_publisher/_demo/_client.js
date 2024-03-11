
// Grab bar container from HTML
const barContainer = document.querySelector('#bars');

// Create a progress bar and append it to the bar container
const createProgressBar = () => {
    const element = document.createElement('div');
    element.classList.add('progress');
    const progress = document.createElement('div');
    element.appendChild(progress);
    barContainer.appendChild(element);
    return { element, progress };
}

// Create a simple WebSocket client wrapper class
class ProgressClient {

    #connect = (props = {}) => {

        const {
            onopen = () => {},
            onclose = () => {},
            onmessage = () => {}
        } = props;

        this.socket = new WebSocket('ws://localhost:8000');
        this.socket.addEventListener('open', onopen);

        // Attempt to reconnect every second if the connection is closed
        this.socket.addEventListener('close', () => {
            onclose();
            setTimeout(() => this.#connect(props), 1000);
        });

        this.socket.addEventListener('message', onmessage);
    }

    constructor(props) {
        this.#connect(props);
    }

    close() {
        this.socket.close();
    }

}


const bars = {} // Track progress bars


// Update the specified progress bar when a message is received from the server
const onProgressUpdate = (event) => {
    const { progress_bar_id, format_dict } = JSON.parse(event.data);
    bars[progress_bar_id].style.width = 100 * (format_dict.n / format_dict.total) + '%';
}

// Create a new WebSocket client
const client = new ProgressClient({ onmessage: onProgressUpdate });

// Declare that the HTML Button should create a new progress bar when clicked
const button = document.querySelector('button');
button.addEventListener('click', () => {
    const { element, progress } = createProgressBar(); // Create a progress bar

    barContainer.appendChild(element); // Render the progress bar

    const progress_bar_id = Math.random().toString(36).substring(7); // Create a unique ID for the progress bar
    bars[progress_bar_id] = progress; // Track the progress bar

    client.socket.send(JSON.stringify({ command: 'start', progress_bar_id })); // Send a message to the server to start the progress bar
})
