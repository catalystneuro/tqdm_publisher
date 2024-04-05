
// Create a simple EventSource client wrapper class
export class EventSourceManager {

    url = 'http://localhost:3768';

    #connect = (props = {}) => {

        const {
            onopen = () => {},
            onclose = () => {},
            onmessage = () => {}
        } = props;

        this.source = new EventSource(`${this.url}/events`);

        this.source.addEventListener('error', function(event) {
            console.error("Failed to connect to event stream.");
        }, false);

        this.source.addEventListener("open", onopen);

        // Attempt to reconnect every second if the event source is closed
        this.source.addEventListener('close', () => {
            onclose();
            setTimeout(() => this.#connect(props), 1000);
        });

        this.source.addEventListener('message', onmessage);
    }

    constructor(props) {
        this.#connect(props);
    }

    async send(data) {
        const copy = { ...data }
        const command = copy.command
        delete copy.command
        return await fetch(`${this.url}/${command}`, {
            method: 'POST',
            body: JSON.stringify(copy),
            headers: {
                'Content-Type': 'application/json'
            }
        })
    }

    close() {
        this.source.close();
    }

}
