// Create a simple WebSocket client wrapper class
export class WebSocketManager {

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
