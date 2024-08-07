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
        var type1 = 'sell';
        var type2 = 'buy';
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
            trans_price: price1
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
                    trans_price: price2
                }),
            });
        })
        .then(response => response.json())
        .then(data => {
            console.log('Second fetch response:', data);
            alert(data.message);
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

    if (document.getElementById('buyRadio').checked) {
        var type = 'buy';
    } else {
        var type = 'sell';
    }


    //console.log(contractDate, price, currentDate, qty, limitPrice, type);

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
            trans_price: price
        }),
    })
        .then(response => response.json())
        .then(data => {
            closeModal();
            closeSpreadModal();
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
    const mMargin = document.getElementById('marginPrice');


    mCloseDate.textContent = contractDate;
    mCurrDate.textContent = currentDate;
    mPrice.textContent = price;
    mMargin.textContent = config.contractMargin.toFixed(2);

    updateOptionsForContract();
    modal.style.display = 'block';
}


function getSingleProfit(contractDate, currentDate) {
    fetch('/getSingleProfit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ contractDate: contractDate, currentDate: currentDate }),
    })
        .then(response => response.json())
        .then(data => {
            console.log("we did the vals, ", data.status);
        })
        .catch(error => console.error('Error fetching wallet number:', error));
}

function getSpreadProfit(contractDate, contractDate1, currentDate) {
    fetch('/getSpreadProfit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ contractDate: contractDate, contractDate1: contractDate1, currentDate: currentDate }),
    })
        .then(response => response.json())
        .then(data => {
            console.log("we did the vals, ", data.status);
        })
        .catch(error => console.error('Error fetching wallet number:', error));
}



function openCloseModal(contractDate, price, currentDate) {
    console.log(contractDate, price, currentDate);
    const modal = document.getElementById('modal');
    const mCloseDate = document.getElementById('mContractDate');
    const mCurrDate = document.getElementById('mCurrentDate');
    const mPrice = document.getElementById('mPrice');
    const mProfit = document.getElementById('mProfit');


    mCloseDate.textContent = contractDate;
    mCurrDate.textContent = currentDate;
    mPrice.textContent = price;

    //Need to call a function for profit calculation ô

    //Need function for actually closing

    //How do we differ spread vs straight contract?
    mProfit.textContent = 5;

    updateOptionsForContract();
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

function updateWalletValues() {
    
    const storedDate = localStorage.getItem('selectedDate');
    fetch('/getWalletValues', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ date: storedDate }),
    })
        .then(response => response.json())
        .then(data => {
            console.log("we did the vals, ", data.status);
        })
        .catch(error => console.error('Error fetching wallet number:', error));

    document.getElementById('loadImg').style.display = 'None';
}

function updateWalletNumber() {
    fetch('/getWallet')
        .then(response => response.json())
        .then(data => {

            const walletNumberElement = document.getElementById('walletInfo');
            const walletNumberSpan = document.querySelector('.wallet_number');
            const margin = document.getElementById('walletMargin');
            const marginSpan = document.querySelector('.dropLabelMargin');
            const unrealized = document.getElementById('walletUnrealized');
            const unrealizedSpan = document.querySelector('.dropLabelUnrealized');

            const marginInfo = parseFloat(data.margin_info.margin);

            //console.log('marginInfo', marginInfo);
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

            
        })
        .catch(error => console.error('Error fetching wallet number:', error));
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
                updateWalletNumber();
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
});

function updateMain() {
    const dateInput = document.getElementById('dateInput');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const dataTable = document.getElementById('dataTable').getElementsByTagName('tbody')[0];

    dateInput.min = config.minDate;
    dateInput.max = config.maxDate;

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
                    dataTable.appendChild(tr);
                });
            });
    }


    dateInput.addEventListener('change', function () {
        localStorage.setItem('selectedDate', dateInput.value);
        fetchDataFunction(dateInput.value);
    });

    prevButton.addEventListener('click', function () {
        const date = new Date(dateInput.value);
        date.setDate(date.getDate() - 1);

        console.log("minDate", config.minDate);
        if (date >= new Date(config.minDate)) {
            dateInput.value = date.toISOString().split('T')[0];
            localStorage.setItem('selectedDate', dateInput.value);
            fetchDataFunction(dateInput.value);
        }
    });

    nextButton.addEventListener('click', function () {
        document.getElementById('loadImg').style.display = 'block';


        const originalDate = new Date(dateInput.value);  // Store the original date
        const date = new Date(originalDate);  // Create a new Date object to increment
        date.setDate(date.getDate() + 1);  // Increment the date by 1 day
        const nextdate = date;
        
        console.log("maxDate", config.maxDate);
        if (nextdate <= new Date(config.maxDate)) {
            const formattedOriginalDate = originalDate.toISOString().split('T')[0];  // Format original date to YYYY-MM-DD
            const formattedNextDate = nextdate.toISOString().split('T')[0];  // Format next date to YYYY-MM-DD
    
            dateInput.value = formattedNextDate;  // Update the date input value
            localStorage.setItem('selectedDate', formattedNextDate);
            fetchDataFunction(formattedNextDate);
    
            // Call the backend to check pending transactions
            fetch('/check_pending', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: formattedOriginalDate,  // Pass the original date
                    next_date: formattedNextDate  // Pass the incremented date
                })
            })
            .then(response => response.json())
            .then(data => {       
                console.log(data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        updateWalletValues();
        updateWalletNumber();

        //document.getElementById('loadImg').style.display = 'None';
    });

    document.getElementById('dataTable').addEventListener('click', function (event) {
        if (event.target && event.target.classList.contains('contractBox') && window.location.pathname.includes('/bought')) {
            console.log("run1");
            openCloseModal(event.target.textContent, event.target.nextElementSibling.textContent, dateInput.value);
        } else if (event.target && event.target.classList.contains('contractBox')) {
            console.log("run2");
            openModal(event.target.textContent, dateInput.value);
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
    }

    fetchDataFunction(dateInput.value);
    updateWalletValues();
}

updateWalletNumber();