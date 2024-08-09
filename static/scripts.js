const config = {
    minDate: '1993-06-25',
    maxDate: '2015-12-11',
    spreadMargin: 2000,
    contractMargin: 6000,
    depositDelay: 3,
    capitalReserve: 0.1,
    marginWarning: 0.1
};

// Function to load config from local storage or use default
function loadConfig() {
    const storedConfig = localStorage.getItem('config');
    if (storedConfig) {
        return JSON.parse(storedConfig);
    }
    return config;
}

// Function to save config to local storage
function saveConfig(newConfig) {
    localStorage.setItem('config', JSON.stringify(newConfig));
}

function giveConfig() {
    fetch('/giveConfig', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
    })
        .then(response => response.json())
        .then(data => {
            console.log(data.status);
        }).catch(error => {
            console.error('Error:', error);
        });
}

window.onload = giveConfig;

function closeModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.style.display = 'none';
    } else {
        console.error('Modal element not found');
    }
}

function closeSpreadModal() {
    const modal = document.getElementById('modal-spread');
    if (modal) {
        modal.style.display = 'none';
    } else {
        console.error('Modal element not found');
    }
}

function buySpread() {

    var contractDate = document.getElementById('sContractDate').dataset.contractDate;
    var contractDate1 = document.getElementById('sContractDate').dataset.contractDate1;

    var price1 = document.getElementById('sPrice').dataset.price1;
    var price2 = document.getElementById('sPrice').dataset.price2;

    var spreadPrice = document.getElementById('sPrice').textContent;
    var currentDate = document.getElementById('sCurrentDate').textContent;
    var qty = document.getElementById('sqtyInput').value;
    var limitPrice = document.getElementById('slimitInput').value;

    if (document.getElementById('sbuyRadio').checked) {
        var type1 = 'sell';
        var type2 = 'buy';
    } else {
        var type1 = 'buy';
        var type2 = 'sell';
    }


    if (wallet < unrealized - (margin + (qty * config.spreadMargin))) {
        alert('You do not have enough funds in your account to cover the margin');
        return;
    }
    console.log(contractDate, contractDate1, price1, price2, spreadPrice, currentDate, qty, limitPrice, type1, type2);

    
    // First fetch with contractDate
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
            type: type1,
            trans_price: price1,
            immediate: spreadPrice === limitPrice
        }),
    })
        .then(response => response.json())
        .then(data => {
            console.log('First fetch response:', data);

            // Second fetch with contractDate1
            return fetch('/buyContract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transactionDate: currentDate,
                    contractDate: contractDate1,
                    qty: qty,
                    limitPrice: limitPrice,
                    status: 'pending',
                    purchaseDate: null,
                    type: type2,
                    trans_price: price2,
                    immediate: spreadPrice === limitPrice
                }),
            });
        })
        .then(response => response.json())
        .then(data => {
            console.log('Second fetch response:', data);
            alert(data.message);
            closeSpreadModal();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing the request.');
        });
}

function buyContract() {

    var contractDate = document.getElementById('mContractDate').textContent;
    var price = document.getElementById('mPrice').textContent;
    var currentDate = document.getElementById('mCurrentDate').textContent;
    var qty = document.getElementById('qtyInput').value;
    var limitPrice = document.getElementById('limitInput').value;

    var wallet = parseFloat(document.getElementById('walletInfo').getAttribute('data-wallet-number'));
    var unrealized = parseFloat(document.getElementById('walletUnrealized').getAttribute('data-wallet-unrealized'));
    var margin = parseFloat(document.getElementById('walletMargin').getAttribute('data-wallet-margin'));


    if (document.getElementById('buyRadio').checked) {
        var type = 'buy';
    } else {
        var type = 'sell';
    }

    console.log("wallet", wallet, "unrealized", unrealized, "margin", margin, "qty", qty, "config", config.contractMargin);
    console.log((margin + (qty * config.contractMargin)));
    if (wallet <= Math.abs(unrealized - (margin + (qty * config.contractMargin)))) {
        alert('You do not have enough funds in your account to cover the margin');
        return;
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
            type: type,
            trans_price: price,
            immediate: price === limitPrice
        }),
    })
        .then(response => response.json())
        .then(data => {
            closeModal();
            closeSpreadModal();
            alert(data.message);
        });
}



function openModal(contractDate, price, currentDate) {
    console.log(contractDate, price, currentDate);
    const modal = document.getElementById('modal');
    const mCloseDate = document.getElementById('mContractDate');
    const mCurrDate = document.getElementById('mCurrentDate');
    const mPrice = document.getElementById('mPrice');
    const mMargin = document.getElementById('marginPrice');


    mCloseDate.textContent = contractDate;
    mCurrDate.textContent = currentDate;
    mPrice.textContent = price;
    mMargin.textContent = config.contractMargin.toFixed(2);

    updateOptionsForContract();
    modal.style.display = 'block';
}



function closeContract() {

    let transID1 = document.getElementById('mContractDate').dataset.transID1;
    let transID2 = document.getElementById('mContractDate').dataset.transID2;
    let qty = document.getElementById('mContractDate').dataset.qty;

    let limitPrice = document.getElementById('mContractDate').dataset.limitPrice;
    let current_price = document.getElementById('mContractDate').dataset.currentPrice;
    let profit = document.getElementById('mContractDate').dataset.profit;
    let limitQty = document.getElementById('mContractDate').dataset.limitQty;
    
    console.log(document.getElementById('mContractDate').dataset);
    console.log("TransID's", transID1, qty, limitPrice , current_price, profit);

    if (current_price === limitPrice) {
        fetch ('/closeContract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transID1: transID1,
                transID2: transID2,
                qty: qty,
                limitQty: limitQty,
                profit: profit
            })
        }).then(response => response.json())
        .then(data => {
            console.log("date", localStorage.getItem('selectedDate'));
            fetchDataFunction(localStorage.getItem('selectedDate'));
            closeModal();
        });

    } else {
        console.log("Ran here");
        console.log("TransID 1", transID1, "TransID 2", transID2, "qty", qty, "lim qty", limitQty, "lim price", limitPrice, "Profit", profit);
        fetch ('/limitClose', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transID1: transID1,
                transID2: transID2,
                qty: qty,
                limitQty: limitQty,
                limitPrice: limitPrice,
                profit: profit
            })
        }).then(response => response.json())
        .then(data => {
            fetchDataFunction(localStorage.getItem('selectedDate'));
            closeModal();
        });
    }

    updateWalletValues();

}


function openCloseModal(contractDate, currentDate, qty, purchase_price, type, transID, current_price) {
    console.log(contractDate, currentDate, qty, purchase_price, type, transID, current_price);

    
    const modal = document.getElementById('modal');
    const mCloseDate = document.getElementById('mContractDate');
    const mCurrDate = document.getElementById('mCurrentDate');
    const mPrice = document.getElementById('mPrice');
    const mProfit = document.getElementById('mProfit');
    const mQty = document.getElementById('qtyInput');
    const mLimit = document.getElementById('limitInput');
    const mCurrPrice = document.getElementById('mCurrPrice');
    const mQtyA = document.getElementById('mQtyA');

    mCloseDate.textContent = contractDate;
    mCurrDate.textContent = currentDate;
    mPrice.textContent = purchase_price;
    mQtyA.textContent = qty;
    mQty.value = qty;
    mLimit.value = '';
    mCurrPrice.textContent = current_price;

    updateOptionsForCloseContract(qty);

    // Add event listeners to combo boxes
    mQty.addEventListener('change', calculateAndDisplayProfit);
    mLimit.addEventListener('change', calculateAndDisplayProfit);

    function calculateAndDisplayProfit() {
        const selectedQty = parseInt(mQty.value);
        const selectedLimitPrice = parseFloat(mLimit.value);


        if (!isNaN(selectedQty) && !isNaN(selectedLimitPrice)) {
            const profit = calculateProfit(selectedQty, selectedLimitPrice, purchase_price, type);
            mProfit.textContent = profit.toFixed(2);
            mCloseDate.dataset.profit = profit;
            mCloseDate.dataset.limitPrice = selectedLimitPrice;
            mCloseDate.dataset.limitQty = selectedQty;
        }
    }

    function calculateProfit(qty, limitPrice, purchasePrice, type) {
        if (type === 'buy') {
            return (limitPrice - purchasePrice) * qty * 1000;
        } else{
            return (purchasePrice - limitPrice) * qty * 1000;
        }
        
    }

    //Need function for actually closing

    if (transID.includes(',')) {
        console.log("runs", transID);
        const [id1, id2] = transID.split(',');
        
        console.log("TransID's", id1, id2);
        
        mCloseDate.dataset.transID1 = id1;
        mCloseDate.dataset.transID2 = id2;
        mCloseDate.dataset.qty = qty;
    
        mCloseDate.dataset.currentPrice = parseFloat(current_price);

    } else {
        console.log("runs not", transID);
        mCloseDate.dataset.transID1 = transID;
        mCloseDate.dataset.transID2 = 'none';
        mCloseDate.dataset.qty = qty;

        if (!isNaN(parseInt(mQty.value))) {
            mCloseDate.dataset.limitQty = parseInt(mQty.value);
        } else {
            mCloseDate.dataset.limitQty = 'none';
        }
        

        mCloseDate.dataset.currentPrice = parseFloat(current_price);
    }
    modal.style.display = 'block';
}

function openSpreadModal(contractDate, contractDate1, price1, price2, spreadPrice, currentDate) {
    console.log("vals", contractDate, spreadPrice, currentDate);

    const modal = document.getElementById('modal-spread');
    const mCloseDate = document.getElementById('sContractDate');
    const mCurrDate = document.getElementById('sCurrentDate');
    const mPrice = document.getElementById('sPrice');
    const mMargin = document.getElementById('sMarginPrice');

    // Check if elements are correctly selected
    if (!mCloseDate || !mCurrDate || !mPrice) {
        console.error("One or more elements not found:", { mCloseDate, mCurrDate, mPrice });
        return;
    }

    let month1 = contractDate.split(' ')[0];
    let month2 = contractDate1.split(' ')[0];
    let year = contractDate1.split(' ')[1];

    mCloseDate.dataset.contractDate = contractDate;
    mCloseDate.dataset.contractDate1 = contractDate1;

    mPrice.dataset.price1 = price1;
    mPrice.dataset.price2 = price2;

    let marginPrice = config.spreadMargin;

    mMargin.dataset.marginPrice = marginPrice;
    mMargin.textContent = marginPrice.toFixed(2);

    mCloseDate.textContent = month1 + '/' + month2 + ' ' + year;
    mCurrDate.textContent = currentDate;
    mPrice.textContent = spreadPrice;


    updateOptionsSpreadContract();
    modal.style.display = 'block';
}

async function updateWalletValues() {
    const storedDate = localStorage.getItem('selectedDate');
    console.log("storedDate", storedDate);
    try {
        const response = await fetch('/getWalletValues', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ date: storedDate }),
        });
        const data = await response.json();
        if (data.message === 'margin call') {
            alert('You have received a margin call. Please deposit funds to cover the margin amount of ' + data.margin_info);
        }
        console.log("we did the vals, ", data.status);
    } catch (error) {
        console.error('Error fetching wallet values:', error);
    }

    await updateWalletNumber();

    document.getElementById('loadImg').style.display = 'none';
}

async function updateWalletNumber() {
    try {


        const response = await fetch('/getWallet');
        const data = await response.json();

        const walletNumberElement = document.getElementById('walletInfo');
        const walletNumberSpan = document.querySelector('.wallet_number');
        const margin = document.getElementById('walletMargin');
        const marginSpan = document.querySelector('.dropLabelMargin');
        const unrealized = document.getElementById('walletUnrealized');
        const unrealizedSpan = document.querySelector('.dropLabelUnrealized');

        const marginInfo = parseFloat(data.margin_info.margin);
        const unrealizedInfo = parseFloat(data.unrealized_info.unrealized);
        const walletInfo = parseFloat(data.wallet_info.wallet_number);

        if (marginSpan && !isNaN(marginInfo)) {
            marginSpan.textContent = marginInfo.toFixed(2);
        }
        if (unrealizedSpan && !isNaN(unrealizedInfo)) {
            unrealizedSpan.textContent = unrealizedInfo.toFixed(2);
        }
        if (walletNumberSpan && !isNaN(walletInfo)) {
            walletNumberSpan.textContent = walletInfo.toFixed(2);
        }
    } catch (error) {
        console.error('Error fetching wallet number:', error);
    }
}


function withdrawFunds() {
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
                getWalletValues();
            });
    }
}

function depositFunds() {
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
        
        valuesList.appendChild(optionElement);
    }

}

function updateOptionsForCloseContract(qty) {
    const settlePrice = parseFloat(document.getElementById('mPrice').textContent);
    const valuesList = document.getElementById('limitList');
    
    const qtyList = document.getElementById('qtyList');
    qtyList.innerHTML = '';

    for (let i = 1; i <= qty; i++) {
        const optionElement = document.createElement('option');
        optionElement.value = i;
        qtyList.appendChild(optionElement);
    }

    // Clear existing options
    valuesList.innerHTML = '';

    // Generate and add new options
    for (let i = -10; i <= 10; i++) {
        const optionValue = (settlePrice + i * 0.1).toFixed(1); // Ensure one decimal place
        const optionElement = document.createElement('option');
        optionElement.value = optionValue;
        
        valuesList.appendChild(optionElement);
    }

}



function updateOptionsSpreadContract() {
    const settlePrice = parseFloat(document.getElementById('sPrice').textContent);
    const valuesList = document.getElementById('limitList');
    //const inputField = document.getElementById('limitInput');


    // Clear existing options
    valuesList.innerHTML = '';

    // Generate and add new options
    for (let i = -10; i <= 10; i++) {
        const optionValue = (settlePrice + i * 0.05).toFixed(2); // Ensure one decimal place
        const optionElement = document.createElement('option');
        optionElement.value = optionValue;
        
        valuesList.appendChild(optionElement);
    }

}


document.addEventListener('DOMContentLoaded', function () {
    loadConfig()
    updateMain();
    colourChange();
});

function colourChange() {
    // Change font color based on value
    const unrealizedElement = document.querySelector('.dropLabelUnrealized');
    const walletElement = document.querySelector('.wallet_number');

    if (unrealizedElement) {
        const unrealizedValue = parseFloat(unrealizedElement.textContent.trim());
        if (unrealizedValue < 0) {
            console.log("negative");
            unrealizedElement.classList.add('negative');
        } else {
            unrealizedElement.classList.add('positive');
        }
    }

    if (walletElement) {
        const walletValue = parseFloat(walletElement.textContent.trim());
        if (walletValue < 0) {
           walletElement.classList.add('negative');
        } else {
            walletElement.classList.add('positive');
        }
    }
}
function fetchDataFunction(date) {
    const currentPath = window.location.pathname;
    if (currentPath.includes('/bought')) {
        console.log("fetching bought", date);
        fetchBought(date);
    } else {
        console.log("fetching data", date);
        fetchData(date);
    }
}

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
        
        const tbody = document.querySelector('#dataTable tbody');
        tbody.innerHTML = ''; // Clear only the tbody

        data.forEach(row => {
            const tr = document.createElement('tr');

            // Manually parse the date string
            const [year, month] = row.CloseDate.split('-');
            const monthNames = ["January", "February", "March", "April", "May", "June",
                                "July", "August", "September", "October", "November", "December"];
            const formattedDate = `${monthNames[parseInt(month, 10) - 1]} ${year}`;
            
            
            tr.innerHTML = ` 
                <td class="contractBox">${formattedDate}</td>
                <td>${row['Settlement Price']}</td>
                <td class="${row.Change < 0 ? 'red' : row.Change > 0 ? 'green' : ''}">${row.Change}</td>
                <td class="${row.percent_change < 0 ? 'red' : row.percent_change > 0 ? 'green' : ''}">${row.percent_change}</td>
                <td class="${row.Spread < 0 ? 'spreadRed' : row.Spread > 0 ? 'spreadGreen' : 'spread'}">${row.Spread}</td>
            `;
            tbody.appendChild(tr); // Append to tbody
        });
    }).catch(error => {
        console.error('Error:', error);
    });
    displayDate(date);
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

            const tbody = document.querySelector('#dataTable tbody');
            tbody.innerHTML = ''; // Clear only the tbody

            data.forEach(row => {
                const tr = document.createElement('tr');
                
                const monthNames = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"];
                
                let formattedDate;
                if (row.contract_date.includes('/')) {
                    const [con1, con2] = row.contract_date.split('/');

                    const [year1, month1] = con1.split('-');
                    const [year2, month2] = con2.split('-');
                    formattedDate = `${monthNames[parseInt(month1, 10) - 1]}/${monthNames[parseInt(month2, 10) - 1]}  ${year1}`;
                } else {
                    const [year, month] = row.contract_date.split('-');
                    formattedDate = `${monthNames[parseInt(month, 10) - 1]}  ${year}`;
                }
                
                tr.setAttribute('trans-id', row.Trans_ID);

                tr.innerHTML = ` 
                <td class="contractBox">${formattedDate}</td>
                <td>${row.limit_price}</td>
                <td>${row['settle_price']}</td>
                <td>${row.status}</td>
                <td>${row.type}</td>
                <td>${row.qty}</td>
                <td>${row.purchase_date}</td>
                <td>${row.purchase_price}</td>
                <td class="${row.change < 0 ? 'red' : row.change > 0 ? 'green' : ''}">${row.change}</td>
                <td class="${row.percent_change < 0 ? 'red' : row.percent_change > 0 ? 'green' : ''}">${row.percent_change}</td>
            `;
                tbody.appendChild(tr); // Append to tbody
            });
        });
    displayDate(date);
    colourChange();
}

function displayDate(dateIn) {
    const dateElement = document.getElementById('current-date');
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    
    // Create a new Date object and set the time to noon to avoid timezone issues
    const date = new Date(dateIn);
    date.setDate(date.getDate() + 1);
    
    const formattedDate = date.toLocaleDateString('en-US', options);
    dateElement.textContent = formattedDate;
}


function updateMain() {
    const dateInput = document.getElementById('dateInput');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const dataTable = document.getElementById('dataTable').getElementsByTagName('tbody')[0];

    dateInput.min = config.minDate;
    dateInput.max = config.maxDate;


    

    dateInput.addEventListener('change', async function () {
        document.getElementById('loadImg').style.display = 'block';
        localStorage.setItem('selectedDate', dateInput.value);
        fetchDataFunction(dateInput.value);
        displayDate(dateInput.value);
        await updateWalletValues();
        await updateWalletNumber();
        document.getElementById('loadImg').style.display = 'none';
    });

    prevButton.addEventListener('click', async function () {
        
        document.getElementById('loadImg').style.display = 'block';
        const date = new Date(dateInput.value);
        date.setDate(date.getDate() - 1);

        console.log("minDate", config.minDate);
        if (date >= new Date(config.minDate)) {
            dateInput.value = date.toISOString().split('T')[0];
            localStorage.setItem('selectedDate', dateInput.value);
            fetchDataFunction(dateInput.value);

            await updateWalletValues();
            await updateWalletNumber();

            displayDate(dateInput.value);
        }

        document.getElementById('loadImg').style.display = 'none';
    });

    nextButton.addEventListener('click', async function () {
        document.getElementById('loadImg').style.display = 'block';
        try {
            const originalDateStr = dateInput.value;  // Get the original date string
            const originalDate = new Date(originalDateStr + 'T00:00:00');  // Parse the date string to avoid time zone issues
            console.log("originalDate", originalDate);

            // Extract year, month, and day components
            const year = originalDate.getFullYear();
            const month = originalDate.getMonth();
            const day = originalDate.getDate();

            // Create a new date object with the incremented day
            const nextdate = new Date(year, month, day + 1);
            console.log("nextdate", nextdate);

            console.log("maxDate", config.maxDate);
            if (nextdate <= new Date(config.maxDate)) {
                console.log("we made it here");
                const formattedOriginalDate = originalDate.toISOString().split('T')[0];  // Format original date to YYYY-MM-DD
                const formattedNextDate = nextdate.toISOString().split('T')[0];  // Format next date to YYYY-MM-DD

                dateInput.value = formattedNextDate;  // Update the date input value
                localStorage.setItem('selectedDate', formattedNextDate);

                try {
                    // Call the backend to check pending transactions
                    const response = await fetch('/check_pending', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            date: formattedOriginalDate,  // Pass the original date
                            next_date: formattedNextDate  // Pass the incremented date
                        })
                    });

                    const data = await response.json();
                    console.log("sending", formattedNextDate);
                    fetchDataFunction(formattedNextDate);

                    // Ensure these functions happen in order after the backend call
                    await updateWalletValues();
                    await updateWalletNumber();
                    colourChange();
                    
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            document.getElementById('loadImg').style.display = 'none';
        } catch (error) {
            console.error('Error:', error);
        }
    });

    document.getElementById('dataTable').addEventListener('click', function (event) {
        if (event.target && event.target.classList.contains('contractBox') && window.location.pathname.includes('/bought') && event.target.nextElementSibling.nextElementSibling.nextElementSibling.textContent === 'Purchased') {
            
            // Get the current element
            let currentElement = event.target; //Contract Date

            let parentRow = currentElement.closest('tr');
            let transID = parentRow.getAttribute('trans-id');

            
            let currentPrice = currentElement.nextElementSibling.nextElementSibling; // Settle Price

            let type = currentElement.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling;
            
            let qty = type.nextElementSibling;
            
            let purchase_price = qty.nextElementSibling.nextElementSibling; 
                

            //              contract month,          current date ,         qty,                 purchase price              type         transID       current price
            openCloseModal(currentElement.textContent, dateInput.value, qty.textContent, purchase_price.textContent, type.textContent, transID, currentPrice.textContent);
        } else if (event.target && event.target.classList.contains('contractBox') && window.location.pathname.includes('/bought') && event.target.nextElementSibling.nextElementSibling.nextElementSibling.textContent === 'Pending') {
            if (confirm("Do you want to cancel this transaction?")) {
                let currentElement = event.target; //Contract Date

                let parentRow = currentElement.closest('tr');


                let transID = parentRow.getAttribute('trans-id');
                

                if (transID.includes('/')) {
                    const [id1, id2] = transID.split('/');
                    
                    console.log("TransID to cancel", id1, id2);
                    cancelTransaction(id1);
                    cancelTransaction(id2);

                } else {

                    console.log("TransID to cancel", transID);
                    cancelTransaction(transID);
                }
            }
        } else if (event.target && event.target.classList.contains('contractBox')) {
            openModal(event.target.textContent, event.target.nextElementSibling.textContent, dateInput.value);
        }
    });

    
    document.getElementById('dataTable').addEventListener('click', function (event) {
        console.log("Click");
        if (event.target.classList.contains('spread') || event.target.classList.contains('spreadRed') || event.target.classList.contains('spreadGreen')) {

            // Get the current element
            let currentElement = event.target;

            // Traverse to the element four columns to the left
            let targetElement = currentElement;
            for (let i = 0; i < 4; i++) {
                if (targetElement.previousElementSibling) {
                    targetElement = targetElement.previousElementSibling;
                } else {
                    console.error('Not enough columns to the left');
                    return;
                }
            }
            
            let monthPrice1 = targetElement.nextElementSibling.textContent;
        
            // Get the parent row of the target element
            let parentRow = targetElement.parentElement;
            if (!parentRow) {
                console.error('Parent row not found');
                return;
            }

            // Get the previous sibling row
            let previousRow = parentRow.previousElementSibling;
            if (!previousRow) {
                console.error('Previous row not found');
                return;
            }

            // Get the corresponding cell in the previous row
            let targetElement1 = previousRow.children[targetElement.cellIndex];
            if (!targetElement1) {
                console.error('Corresponding cell not found in the previous row');
                return;
            }

            let monthPrice2 = targetElement1.nextElementSibling.textContent;

            console.log("MonthPrice1", monthPrice1);   
            console.log("MonthPrice2", monthPrice2);
            openSpreadModal(targetElement1.textContent, targetElement.textContent, monthPrice1, monthPrice2, event.target.textContent, dateInput.value);
        }
    });

    
    const storedDate = localStorage.getItem('selectedDate');
    if (storedDate) {
        dateInput.value = storedDate;
        
    } else {
        dateInput.value = config.maxDate;
        localStorage.setItem('selectedDate', config.maxDate);
    }

    fetchDataFunction(dateInput.value);
    updateWalletValues();
}

function cancelTransaction(transID) {
    fetch('/cancelTransaction', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ transID: transID }),
    })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            updateWalletNumber();
        });
}
