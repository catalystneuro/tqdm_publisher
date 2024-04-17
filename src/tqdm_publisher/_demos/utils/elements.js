
const BARS = {} // Track progress bars
const REQUESTS = {} // Track request containers

export const barContainer = document.querySelector('#bars');

// Create a progress bar and append it to the bar container
export const createProgressBar = (requestContainer = barContainer) => {

    const container = document.createElement('div');
    container.classList.add('bar');

    const row1 = document.createElement('div');
    const row2 = document.createElement('div');

    const element = document.createElement('div');
    element.classList.add('progress');
    const progress = document.createElement('div');

    const readout = document.createElement('small');
    element.append(progress);

    row1.append(element, readout);

    const descriptionEl = document.createElement('small');
    row2.append(descriptionEl);

    container.append(row1, row2);

    requestContainer.appendChild(container); // Render the progress bar


    const update = ( format_dict, { request_id, progress_bar_id }  = {}) => {

        const { total, n, elapsed, rate, prefix } = format_dict;

        const percent = 100 * (n / total);
        progress.style.width = `${percent}%`

        readout.innerText = `${n} / ${total} (${percent.toFixed(1)}%)`;


        const remaining = rate && total ? (total - n) / rate : 0; // Seconds

        descriptionEl.innerText = `${prefix ? `${prefix} — ` : ''}${elapsed.toFixed(1)}s elapsed, ${remaining.toFixed(1)}s remaining`;
    }


    return {
        element,
        description: descriptionEl,
        progress,
        readout,
        container,
        update
    };
}

// Create + render a progress bar
export function getBar (request_id, progress_bar_id) {

    if (BARS[progress_bar_id]) return BARS[progress_bar_id];

    const bar = createProgressBar(getRequestContainer(request_id).bars);

    const { container } = bar;
    container.setAttribute('data-small', request_id !== progress_bar_id); // Add a small style to the progress bar if it is not the main request bar

    return BARS[progress_bar_id] = bar;

}

export function getRequestContainer(request_id) {
    const existing = REQUESTS[request_id]
    if (existing) return existing;

    // Create a new container for the progress bar
    const container = document.createElement('div');
    container.id = request_id;
    container.classList.add('request-container');

    const header = document.createElement('header');

    const firstHeaderContainer = document.createElement('div');
    const h2 = document.createElement('h2');
    h2.innerText = `Request ID: ${request_id}`;

    const description = document.createElement('small');

    firstHeaderContainer.append(h2, description);
    header.append(firstHeaderContainer);

    const barsElement = document.createElement('div');
    barsElement.classList.add('bar-container');

    container.append(header, barsElement);
    barContainer.append(container);

    return REQUESTS[request_id] = {
        header: h2,
        description,
        bars: barsElement,
        element: container
    };


}
