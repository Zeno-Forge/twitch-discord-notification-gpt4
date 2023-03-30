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

function fetchSubscriptions() {
    fetch('/get-subscriptions')
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          console.error('Error fetching subscriptions:', response.status);
          throw new Error('Error fetching subscriptions');
        }
      })
      .then((subscriptions) => {
        const table = document.getElementById('subscriptionsTable');
        // Clear the existing table rows, except for the header row
        for (let i = table.rows.length - 1; i > 0; i--) {
            table.deleteRow(i);
        }
  
        // Populate the table with the received subscriptions
        subscriptions.forEach((sub) => {
          const row = document.createElement('tr');
          row.id = "subscription-row-" + sub.id;

          const streamerNameCell = document.createElement('td');
          streamerNameCell.textContent = sub.username;
          row.appendChild(streamerNameCell);
  
          const eventTypeCell = document.createElement('td');
          eventTypeCell.textContent = sub.type;
          row.appendChild(eventTypeCell);

          const dateTypeCell = document.createElement('td');
          dateTypeCell.textContent = sub.created_at;
          row.appendChild(dateTypeCell);

          const callbackCell = document.createElement('td');
          callbackCell.textContent = sub.transport.callback;
          row.appendChild(callbackCell);

          const statusCell = document.createElement('td');
          statusCell.textContent = sub.status;
          row.appendChild(statusCell);
  
          const removeButtonCell = document.createElement('td');
          const removeButton = document.createElement('button');
          removeButton.textContent = 'X';
          removeButton.onclick = () => removeSubscription(sub.id);
          removeButtonCell.appendChild(removeButton);
          row.appendChild(removeButtonCell);
  
          table.appendChild(row);
        });
      })
      .catch((error) => {
        console.error('Error populating subscriptions table:', error);
      });
  }
  
  // Call the fetchSubscriptions function when the page loads
  document.addEventListener('DOMContentLoaded', fetchSubscriptions);  
  document.addEventListener('DOMContentLoaded', updateEventSubInfo);