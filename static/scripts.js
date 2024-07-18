

function closeModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.style.display = 'none';
    } else {
        console.error('Modal element not found');
    }
}

function buyContract() {

    var contractDate = document.getElementById('mContractDate').textContent;
    var price = document.getElementById('mPrice').textContent;
    var currentDate = document.getElementById('mCurrentDate').textContent;
    var qty = document.getElementById('qtyInput').value;
    var limitPrice = document.getElementById('limitInput').value;

    if (document.getElementById('buyRadio').checked) {
        var type = 'buy';
    } else {
        var type = 'sell';
    }
    

    console.log(contractDate, price, currentDate, qty, limitPrice, type);
    
    fetch('/buyContract', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            transactionDate: currentDate,
            contractDate: contractDate,
            qty: qty,
            limitPrice: limitPrice,
            status: 'pending',
            purchaseDate: null,
            type: type
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
    });
}

function sellContract() {

    var contractDate = document.getElementById('mContractDate').textContent;
    var price = document.getElementById('mPrice').textContent;
    var currentDate = document.getElementById('mCurrentDate').textContent;

    fetch('/sell', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            contractDate: contractDate,
            type: 'sell',
            price: price,
            currentDate: currentDate
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
    });
}



function openModal(contractDate, price, currentDate) {
    console.log(contractDate, price, currentDate);
    const modal = document.getElementById('modal');
    const mCloseDate = document.getElementById('mContractDate');
    const mCurrDate = document.getElementById('mCurrentDate');
    const mPrice = document.getElementById('mPrice');
    mCloseDate.textContent = contractDate;
    mCurrDate.textContent = currentDate;
    mPrice.textContent = price;

    updateOptionsForContract();
    modal.style.display = 'block';
}

function updateWalletNumber() {
    fetch ('/getWallet')
        .then(response => response.json())
        .then(data => {
            const walletNumberElement = document.getElementById('walletInfo');
            const walletNumberSpan = document.querySelector('.wallet_number');
            if (walletNumberElement) {
                walletNumberElement.dataset.walletNumber = data.wallet_number.toFixed(2);
            }
            if (walletNumberSpan) {
                walletNumberSpan.textContent = data.wallet_number.toFixed(2);
            }
        })
        .catch(error => console.error('Error fetching wallet number:', error));
}

// Also update on page load
updateWalletNumber();

function withdrawFunds(){
    const amount = parseFloat(prompt('Enter the amount you want to deposit:'));
    const wallet_number = parseFloat(document.getElementById('walletInfo').dataset.walletNumber);

    if (amount > wallet_number) {
        alert('You do not have enough funds to withdraw');
    } else if (amount !== null) {
        fetch('/withdraw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ amount: amount }),
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            updateWalletNumber();
        });
    }
} 

function depositFunds(){
    const amount = prompt('Enter the amount you want to deposit:');

    if (amount !== null) {
        fetch('/deposit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ amount: amount }),
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            updateWalletNumber();
        });
    }
}

function restart() {
    var confirmation = confirm('Are you sure you want to restart?');
    if (confirmation) {
        fetch('/restart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            updateWalletNumber();

            const currentPath = window.location.pathname;

            if (currentPath.includes('/bought')) {
                const dataTable = document.getElementById('dataTable').getElementsByTagName('tbody')[0]
                dataTable.innerHTML = '';
            }
            
        });
    }
}


function updateOptionsForContract() {
    const settlePrice = parseFloat(document.getElementById('mPrice').textContent);
    const valuesList = document.getElementById('limitList');
    //const inputField = document.getElementById('limitInput');

    
    // Clear existing options
    valuesList.innerHTML = '';
    
    // Generate and add new options
    for (let i = -10; i <= 10; i++) {
        const optionValue = (settlePrice + i * 0.1).toFixed(1); // Ensure one decimal place
        const optionElement = document.createElement('option');
        optionElement.value = optionValue;
        console.log(optionValue);
        valuesList.appendChild(optionElement);
    }

}

document.addEventListener('DOMContentLoaded', function() {
    updateMain();
});

function updateMain() {
    const dateInput = document.getElementById('dateInput');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const dataTable = document.getElementById('dataTable').getElementsByTagName('tbody')[0];

    const minDate = '1993-06-25';
    const maxDate = '2015-12-11';
    dateInput.min = minDate;
    dateInput.max = maxDate;

    const currentPath = window.location.pathname;
    const fetchDataFunction = currentPath.includes('/bought') ? fetchBought : fetchData;

    function fetchData(date) {
        fetch('/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ date: date }),
        })
        .then(response => response.json())
        .then(data => {
            dataTable.innerHTML = '';
            data.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML =` 
                    <td class="contractBox">${row.CloseDate}</td>
                    <td>${row['Settlement Price']}</td>
                    <td class="${row.Change < 0 ? 'red' : row.Change > 0 ? 'green' : ''}">${row.Change}</td>
                    <td class="${row.percent_change < 0 ? 'red' : row.percent_change > 0 ? 'green' : ''}">${row.percent_change}</td>
                    <td class="${row.Spread < 0 ? 'spreadRed' : row.Spread > 0 ? 'spreadGreen' : 'spread'}">${row.Spread}</td>
                `;
                dataTable.appendChild(tr);
            });
        });
    }

    function fetchBought(date) {
        fetch('/boughtData', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ date: date }),
        }).then(response => response.json())
            .then(data => {
                dataTable.innerHTML = '';
                data.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = ` 
                    <td class="contractBox">${row.contract_date}</td>
                    <td>${row.limit_price}</td>
                    <td>${row['settle_price']}</td>
                    <td class="${row.change < 0 ? 'red' : row.change > 0 ? 'green' : ''}">${row.change}</td>
                    <td class="${row.percent_change < 0 ? 'red' : row.percent_change > 0 ? 'green' : ''}">${row.percent_change}</td>
                    <td>${row.status}</td>
                    <td>${row.purchase_date}</td>
                `;
                    dataTable.appendChild(tr);
                });
            });
    }
    

    dateInput.addEventListener('change', function() {
        fetchData(dateInput.value);
    });

    prevButton.addEventListener('click', function() {
        const date = new Date(dateInput.value);
        date.setDate(date.getDate() - 1);
        if (date >= new Date(minDate)) {
            dateInput.value = date.toISOString().split('T')[0];
            fetchDataFunction(dateInput.value);
        }
    });

    nextButton.addEventListener('click', function() {
        const date = new Date(dateInput.value);
        date.setDate(date.getDate() + 1);
        if (date <= new Date(maxDate)) {
            dateInput.value = date.toISOString().split('T')[0];
            fetchDataFunction(dateInput.value);
        }
    });

    document.getElementById('dataTable').addEventListener('click', function(event) {
        if (event.target && event.target.classList.contains('contractBox')) {
            openModal(event.target.textContent, event.target.nextElementSibling.textContent, dateInput.value);
        }
    });
    
    // Set the date input to max date on load
    dateInput.value = maxDate;
    fetchDataFunction(maxDate);
}