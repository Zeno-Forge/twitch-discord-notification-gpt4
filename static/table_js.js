// static/table_js.js
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
            reloadSubscriptionTable();
            window.parent.postMessage("", "*");
        } else {
            alert('Failed to remove subscription.');
        }
    } catch (error) {
        alert('An error occurred while removing the subscription.' + error);
    }
}

function reloadSubscriptionTable() {
        window.location.reload();
}