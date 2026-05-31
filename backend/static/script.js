async function predict() {

    const data = {
        commodity: document.getElementById("commodity").value,
        date: document.getElementById("date").value,
        p_min: Number(document.getElementById("p_min").value),
        p_max: Number(document.getElementById("p_max").value)
    };

    if (data.p_min > data.p_max) {
        alert("Minimum price cannot be greater than Maximum price");
        return;
    }

    try {

        const response = await fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.error) {
            document.getElementById("result").innerText = result.error;
            return;
        }

        document.getElementById("result").innerText =
            `Predicted Modal Price at the market ${result.market_id} is: ₹${result.predicted_modal_price}`;

    }
    catch (error) {

        document.getElementById("result").innerText =
            "Unable to connect to server.";

        console.error(error);
    }
}