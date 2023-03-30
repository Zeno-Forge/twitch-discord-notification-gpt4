// static/main.js
const form = document.getElementById('subscribe-form');
const messageContainer = document.getElementById('message');

async function updateEventSubInfo() {
    try {
        const response = await fetch('/eventsub-info');
        const { total_cost, max_total_cost } = await response.json();
        document.getElementById('total_cost').textContent = total_cost;
        document.getElementById('max_total_cost').textContent = max_total_cost;
    } catch (error) {
        console.error('Failed to update EventSub subscription info:', error);
    }
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(form);

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const { error } = await response.json();
            messageContainer.textContent = error;
            messageContainer.style.color = 'red';
        } else {
            const { success } = await response.json();
            messageContainer.textContent = success;
            messageContainer.style.color = 'green';
            updateEventSubInfo();
        }
    } catch (error) {
        messageContainer.textContent = 'An error occurred while subscribing.';
        messageContainer.style.color = 'red';
    }
});

async function removeSubscription(id) {
    console.log("removeSubscription called with id:", id);
    const url = `/remove-subscription`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `id=${id}`
        });

        if (response.ok) {
            document.getElementById(`subscription-row-${id}`).remove();
            updateEventSubInfo()
        } else {
            alert('Failed to remove subscription.');
        }
    } catch (error) {
        alert('An error occurred while removing the subscription.');
    }
    
    
}