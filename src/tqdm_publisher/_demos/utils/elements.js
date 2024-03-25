export const barContainer = document.querySelector('#bars');

// Create a progress bar and append it to the bar container
export const createProgressBar = (container = barContainer) => {
    const element = document.createElement('div');
    element.classList.add('progress');
    const progress = document.createElement('div');
    element.appendChild(progress);
    container.appendChild(element); // Render the progress bar
    return progress;
}
