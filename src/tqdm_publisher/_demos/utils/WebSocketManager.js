// Create a simple WebSocket client wrapper class
export class WebSocketManager {

    #connect = (props = {}, maxTries = null) => {

        const {
            onopen = () => {},
            onclose = () => {},
            onmessage = () => {}
        } = props;

        let tries = 0;
        this.socket = new WebSocket('ws://localhost:3768');
        this.socket.addEventListener('open', onopen);

        // Attempt to reconnect every second if the connection is closed
        this.socket.addEventListener('close', () => {
            onclose();
            console.log('Connection closed', tries, maxTries);
            if (maxTries && tries >= maxTries) return;
            tries++;
            setTimeout(() => this.#connect(props), 1000);
        });

        this.socket.addEventListener('message', onmessage);
    }

    constructor(props) {
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
