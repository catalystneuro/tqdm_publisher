// Create a simple WebSocket client wrapper class
export class WebSocketManager {

    #tries = 0;
    #maxTries = null;

    #connect = (props = {}) => {

        const {
            onopen = () => {},
            onclose = () => {},
            onmessage = () => {}
        } = props;

        this.socket = new WebSocket('ws://localhost:3768');
        this.socket.addEventListener('open', onopen);

        // Attempt to reconnect every second if the connection is closed
        this.socket.addEventListener('close', () => {
            onclose();
            if (this.#maxTries && this.#tries >= this.#maxTries) return;
            this.#tries++;
            setTimeout(() => this.#connect(props), 1000);
        });

        this.socket.addEventListener('message', onmessage);
    }

    constructor(props, maxTries) {
        this.#maxTries = maxTries
        this.#connect(props);
    }

    send(data) {
        if (this.socket.readyState !== WebSocket.OPEN) return false // Ignore messages if the socket is not open
        this.socket.send(JSON.stringify(data));
    }

    close() {
        this.socket.close();
    }

}
