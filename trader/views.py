from typing import cast
from django.http import request
from django.http.response import *
from trader.models import Stock
from django.shortcuts import get_list_or_404, get_object_or_404, render, redirect
from .forms import StockForm, TickerForm
from .models import Account, Stock, Transaction
from .finance import getStockData, stockPlot
from .dates import getDate
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout, login
import json

# Create your views here.
def home(request):
    account = Account.getAccount(1)
    balance = account.balance
    username = account.username
    stocks = Stock.getStocks()
    investValue = calcValue()
    showPortfolio = True
    showStock = False
    showPlot = False
    if request.method == "POST":
        tickerSymbol = request.POST.get('ticker')
        startDate = getDate('year')
        endDate = getDate()
        stock = getStockData(tickerSymbol, startDate, endDate)
        if stock['today'] < 0:
            todayColor = 'style=color:--red;'
        else:
            todayColor = 'style=color:green;'
        showPortfolio = False
        showStock = True
        showPlot = True
        context = {
            'username': username, 
            'balance': round(balance, 2), 
            'stocks': stocks, 
            'showStock': showStock, 
            'showPlot': showPlot, 
            'showPortfolio' : showPortfolio, 
            'stock': stock,
            'todayColor': todayColor
            }
        return render(request, 'trader/home.html', context)
    context = {
        'username': username, 
        'balance': round(balance, 2), 
        'investValue': round(investValue,2),
        'stocks': stocks, 
        'showStock': showStock,
        'showPlot':  showPlot,
        'showPortfolio' : showPortfolio
        }
    return render(request, 'trader/home.html', context)

def calcValue():
    #stocks = Stock.getStocks()

    transactions = Transaction.getTransactions()
    value = 0
    total = 0

    for tran in transactions:
        value = tran.price * tran.shares
        total += value
    
    return total

        

def account(request):
    account = Account.getAccount(1)
    balance = account.balance
    username = account.username
    password = account.password
    firstname = account.first_name
    lastname = account.last_name
    investValue = calcValue()
    transactions = Transaction.getTransactions()
    context = {'username': username, 'firstname': firstname, 'lastname': lastname, 'password': password, 'balance': round(balance, 2), 'transactions': transactions, 'investValue': investValue}
    return render(request, 'trader/account.html', context)

def resetAccount(request):
    Account.resetBalance()
    Stock.deleteAllStock()
    Transaction.deleteAllTransactions()
    return redirect('/account')


def buyStock(request):
    account = Account.getAccount(1)
    balance = account.balance
    resp = {}
    
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            symbol = data['symbol']
            name = data['name']
            shares = data['shares']
            price = data['price']
            if balance >= int(float(price)) * int(float(shares)):
                account.balance = balance - int(float(price)) * int(float(shares))
                account.save()
                Stock.createStock(symbol, name, shares, accountId = 1)
                Transaction.createTransaction('Buy', symbol, shares, price, accountId = 1)
                resp['result'] = 'Success'
                resp['message'] = 'You have successfully ordered shares'
            else:
                resp['result'] = 'Failure'
                resp['message'] = 'Insufficent Funds'
        return JsonResponse(resp)

    except Exception as e:
        resp['result'] = 'Error'
        resp['message'] = e
        return JsonResponse(resp)

def sellStock(request):
    account = Account.getAccount(1)
    balance = account.balance
    resp = {}

    try:
        if request.method == "POST":
            data = json.loads(request.body)
            print("Json=" + str(data))
            symbol = data['symbol']
            shares = data['shares']
            price = data['price']
            account.balance = balance + int((float(price)) * int(float(shares)))
            account.save()
            Stock.deleteStock(symbol, shares)
            Transaction.createTransaction('Buy', symbol, shares, price, accountId = 1)
            resp['result'] = 'Success'
            resp['message'] = 'You have successfully ordered shares'
        return JsonResponse(resp)

    except Exception as e:
        resp['result'] = 'Error'
        resp['message'] = e
        return JsonResponse(resp)


def login_view(request):
    user = authenticate(request, username='root', password='password123')
    if user is not None:
        print('username is authenticated')
        login(request, user)
        return redirect('/')


def logout_view(request):
    logout(request)
    return redirect('/')
