#! /usr/bin/python3.5
import os.path
import sys
import time
from threading import Timer
import asyncio
import datetime
import keyboard
import pymssql
from pyA20.gpio import gpio
from pyA20.gpio import port

button_pressed = 0


class Configuration:
    IP = "adress"
    InfoServer = "ProcessingServer"
    TransactionServer = "BackendServer"
    User = "username"
    Password = "password"

    ArtCode1 = '1250'
    ArtCode2 = '1250'
    ArtCode3 = '1250'
    ArtCode4 = '1250'

    SareaID = 200
    #Number for Sales Area
    SystemID = 300
    #Number for device
    CurrencyID = 6
    #Currency number in Market+
    AccountTypeID = 3
    TransTypeID = 0
    AutoCreateAccountID = 0
    AccountDocSourceID = 0
    deflagID = 0

    LogPath = "gdrive/"

    pingTime = 2
    Green = port.PA10
    Red = port.PA7

    Button1 = port.PA18
    Coffee1 = port.PA20
    Button2 = port.PG8
    Coffee2 = port.PA13
    Button3 = port.PG9
    Coffee3 = port.PA2
    Button4 = port.PG6
    Coffee4 = port.PA8
    Button5 = port.PG7

    green_status_stop = False

def writeLogError(line):
    try:
        now = datetime.datetime.now()
        file_name = Configuration.LogPath + str(Configuration.SystemID) + "_errors.log"
        if os.path.exists(Configuration.LogPath) == False:
            os.makedirs(Configuration.LogPath)
        if os.path.exists(file_name):
            f = open(file_name, "a+")
        else:
            f = open(file_name, "w+")
        f.write(str(now) + " - " + line + "\n")
        f.close()
    except Exception as init:
        print(str(init) + str(now))


def writeLogBill(line):
    try:
        now = datetime.datetime.now()
        file_name = Configuration.LogPath + str(Configuration.SystemID) + "_bill.log.txt"

        if os.path.exists(Configuration.LogPath) == False:
            os.makedirs(Configuration.LogPath)
        if os.path.exists(file_name):
            f = open(file_name, "a+")
        else:
            f = open(file_name, "w+")
        f.write(str(now) + " - " + line + "\n")
        f.close()
    except Exception as init:
        print(str(init) + str(now))


def enablePin(pinnumber):
    PIN = pinnumber
    argvs = sys.argv
    argc = len(argvs)
    if argc == 2:
        PIN = int(argvs[1])
    gpio.setcfg(PIN, gpio.OUTPUT)
    gpio.output(PIN, True)


def disablePin(pinnumber):
    PIN = pinnumber
    argvs = sys.argv
    argc = len(argvs)
    if argc == 2:
        PIN = int(argvs[1])
    gpio.setcfg(PIN, gpio.OUTPUT)
    gpio.output(PIN, False)


def pourCoffee(pinnumber):
    enablePin(pinnumber)
    time.sleep(0.5)
    disablePin(pinnumber)
    pouringCoffee()


def pouringCoffee():
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(seconds=15)
    end_timer = addSecs(end_time, 300)
    print(start_time)
    while True:
        current_time = datetime.datetime.now()
        current_timer = addSecs(current_time, 300)

        disablePin(Configuration.Red)
        enablePin(Configuration.Green)
        time.sleep(0.5)
        disablePin(Configuration.Green)
        enablePin(Configuration.Red)
        time.sleep(0.5)

        if current_timer == end_timer:
            Configuration.green_status_stop = False
            print(datetime.datetime.now())
            return



def statusOnline():
    disablePin(Configuration.Red)
    enablePin(Configuration.Green)
    time.sleep(Configuration.pingTime)
    disablePin(Configuration.Green)
    time.sleep(Configuration.pingTime)


def statusOffline():
    disablePin(Configuration.Green)
    enablePin(Configuration.Red)


def statusNoCard():
    disablePin(Configuration.Green)
    enablePin(Configuration.Red)
    time.sleep(2)
    disablePin(Configuration.Red)

def statusNoMoney():
    disablePin(Configuration.Green)
    enablePin(Configuration.Red)
    time.sleep(5)
    disablePin(Configuration.Red)


def button5action():
    state2 = gpio.input(Configuration.Button2)
    state4 = gpio.input(Configuration.Button4)
    if state2 == button_pressed:
        pourCoffee(Configuration.Coffee2)
    if state4 == button_pressed:
        pourCoffee(Configuration.Coffee4)

def addSecs(tm, secs):
    fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    fulldate = fulldate + datetime.timedelta(seconds=secs)
    return fulldate.time()


def init():
    gpio.init()

    gpio.setcfg(Configuration.Green, gpio.OUTPUT)
    gpio.setcfg(Configuration.Red, gpio.OUTPUT)

    gpio.setcfg(Configuration.Button1, gpio.INPUT)
    gpio.pullup(Configuration.Button1, 0)
    gpio.pullup(Configuration.Button1, gpio.PULLDOWN)
    gpio.pullup(Configuration.Button1, gpio.PULLUP)
    gpio.setcfg(Configuration.Coffee1, gpio.OUTPUT)

    gpio.setcfg(Configuration.Button2, gpio.INPUT)
    gpio.pullup(Configuration.Button2, 0)
    gpio.pullup(Configuration.Button2, gpio.PULLDOWN)
    gpio.pullup(Configuration.Button2, gpio.PULLUP)
    gpio.setcfg(Configuration.Coffee2, gpio.OUTPUT)

    gpio.setcfg(Configuration.Button3, gpio.INPUT)
    gpio.pullup(Configuration.Button3, 0)
    gpio.pullup(Configuration.Button3, gpio.PULLDOWN)
    gpio.pullup(Configuration.Button3, gpio.PULLUP)
    gpio.setcfg(Configuration.Coffee3, gpio.OUTPUT)

    gpio.setcfg(Configuration.Button4, gpio.INPUT)
    gpio.pullup(Configuration.Button4, 0)
    gpio.pullup(Configuration.Button4, gpio.PULLDOWN)
    gpio.pullup(Configuration.Button4, gpio.PULLUP)
    gpio.setcfg(Configuration.Coffee4, gpio.OUTPUT)

    gpio.setcfg(Configuration.Button5, gpio.INPUT)
    gpio.pullup(Configuration.Button5, 0)
    gpio.pullup(Configuration.Button5, gpio.PULLDOWN)
    gpio.pullup(Configuration.Button5, gpio.PULLUP)


def justDoIt(card):
    now = datetime.datetime.now()
    hna = str(now.year) + str(now.timetuple().tm_yday)
    c = pymssql.connect(Configuration.IP, Configuration.User, Configuration.Password, "tempdb")
    cursor = c.cursor()

    try:
        cardCode = card
        try:
            checkCardRes = float(card)
        except:
            return False
        if checkCardRes == False:
            return False
        data1 = {0: "nocard"}
        try:

            query = "SELECT b.DCARDNAME, a.ACCOUNTSUM / 100 AS Expr1, b.LOCKED, b.DELFLAG, a.ACCOUNTTYPEID, a.CLNTID " + \
                    "FROM [" + Configuration.InfoServer + "].[dbo].[ACCOUNTROOT] a, [" + Configuration.InfoServer + "].[dbo].[DCARD] b " + \
                    "WHERE a.CLNTID = b.CLNTID AND b.DCARDCODE = '" + cardCode + "'"
            cursor.execute(query)
            r = cursor.fetchone()
            if r[2] == 1:
                data1[3] = "lock"
            if r[3] == 1:
                data1[4] = "del"
            if r[4] == 3:
                data1[0] = str(r[1])
            data1[1] = str(r[0])
            data1[5] = str(r[5])
            
            writeLogError(str(r))

        except:
            data1[0] = "error"

        dataget = data1

        if str(dataget[0]) == "error":
            errorLine = "Error" + str(cardCode) + " - " + str(dateget)
            writeLogError(errorLine)
            statusNoCard()
            return
        elif str(dataget[0]) == "nocard":
            errorLine = "Несуществующий номер карты" + str(cardCode) + " - " + str(dateget)
            writeLogError(errorLine)
            statusNoCard()
            return
        elif 3 in dataget:
            errorLine = "Карта заблокирована" + str(cardCode) + " - " + str(dateget)
            writeLogError(errorLine + str(cardCode))
            statusNoCard()
            return
        elif 4 in dataget:
            errorLine = "Карта заблокирована" + str(cardCode) + " - " + str(dateget)
            writeLogError(errorLine)
            statusNoCard()
            return
    except Exception as inst:
        writeLogError(inst)

    Configuration.green_status_stop = True
    print(Configuration.green_status_stop)
    enablePin(Configuration.Green)
    """
    Waiting for user to press a button
    """

    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(seconds=10)
    end_timer = addSecs(end_time, 300)

    while True:
        current_time = datetime.datetime.now()
        current_timer = addSecs(current_time, 300)

        state1 = gpio.input(Configuration.Button1)
        state2 = gpio.input(Configuration.Button2)
        state3 = gpio.input(Configuration.Button3)
        state4 = gpio.input(Configuration.Button4)
        state5 = gpio.input(Configuration.Button5)

        if current_timer == end_timer:
            Configuration.green_status_stop = False
            print(Configuration.green_status_stop)
            return
        if state1 == button_pressed:
            artCode = Configuration.ArtCode1
            break
        if state2 == button_pressed:
            artCode = Configuration.ArtCode2
            break
        if state3 == button_pressed:
            artCode = Configuration.ArtCode3
            break
        if state4 == button_pressed:
            artCode = Configuration.ArtCode4
            break
        if state5 == button_pressed:
            while current_timer <= end_timer:
                button5action()
                time.sleep(0.05)
        time.sleep(0.05)

    try:
        SYSTEMID = str(Configuration.SystemID)
        SAREAID = str(Configuration.SareaID)
        SESSID = str(hna)
        SALESNUM = 1
        SRECNUM = 1
        CASHIERID = 1

        snmax = "SELECT MAX(salesnum) FROM DataServer.dbo.sales WHERE SYSTEMID = " + str(SYSTEMID)
        cursor.execute(snmax)
        r = cursor.fetchone()
        if r[0] is not None:
            SALESNUM = r[0] + 1
    except Exception as inst:
        writeLogError(inst)

    try:
        srmax = "SELECT MAX(SRECNUM) FROM DataServer.dbo.sales" \
                " WHERE SYSTEMID = " + SYSTEMID + " AND SESSID = " + SESSID
        cursor.execute(srmax)
        r = cursor.fetchone()
        if r[0] is not None:
            SRECNUM = r[0] + 1
    except Exception as inst:
        writeLogError(inst)

    try:
        if artCode is None:
            return

        ArtCode = artCode
        ArtName = ""
        ArtPackName = 1
        ArtPrice = 1
        ArtPackId = 1

        q = "use dataserver " + \
            "select artcode, artname, packname, pack.packid, packprice FROM art " + \
            "left join pack on (art.artid = pack.artid) " + \
            "left join packprc on (pack.packid = packprc.packid) " + \
            "where art.delflag = 0 and pack.delflag = 0 and packprc.delflag = 0 and art.artcode = " + ArtCode
        cursor.execute(q)
        r = cursor.fetchone()

        ArtName = str(r[1])
        ArtPackName = str(r[2])
        ArtPackId = str(r[3])
        ArtPrice = str(r[4])
    except Exception as inst:
        writeLogError(inst)

    try:
        cardCode = str(card)
        clientId = 0
        clientName = ""
        clientSumm = 0

        balq = "use ProcessingServer; " \
               "select accountsum, a.clntid, c.clntname  FROM accountroot a " \
               "left join dcard d on (a.clntid = d.clntid)" \
               "left join clnt c on (a.clntid = c.clntid)" \
               "where isblocked = 0 and isclosed = 0 and  ispayment = 1 " \
               "and d.dcardcode = '" + str(cardCode) + "' and accounttypeid = 3"

        cursor.execute(balq)
        r = cursor.fetchone()
        clientSumm = str(r[0])
        clientId = str(r[1])
        clientName = str(r[2])

        if int(clientSumm) < int(ArtPrice):
            statusNoMoney()
            return

    except Exception as inst:
        writeLogError(inst)

    ActualSalesCount = 0
    PRCLEVELID = 1
    SALESTIME = ""
    FRECNUM = 0
    SALESCANC = 0
    SALESREFUND = 0

    DELFLAG = 0
    CLNTID = "null"
    UPDATENUM = 0
    SALESTAG = 0
    SALESBARC = "''"
    SALESDISC = 0
    SALESPRICE = 0
    SALESCOUNT = 1
    SALESSUM = 1
    BONUSSUM = 0

    SALESCODE = 1
    SALESTYPE = 1
    SALESFLAGS = 0
    PACKNAME = ""
    PACKCOUNT = 1
    SALESATTRI = 0
    SALESATTRS = 0
    SALESEXTCOUNT = 0
    SALESBONUS = 0
    SYSTEMTYPE = 2
    DCARDCODE = ""

    def MakeIns(level):
        ins0 = "INSERT INTO [DataServer].[dbo].[SALES]" \
               "([SALESNUM], [SESSID], [SYSTEMID], [SAREAID], [PRCLEVELID], [TXTBINID], [SALESTAG], " \
               "[SALESTIME], [FRECNUM], [SRECNUM], [SALESBARC], [SALESDISC], [SALESPRICE], [SALESSUM], " \
               "[BONUSSUM], [SALESCOUNT], [SALESCODE], [SALESTYPE], [SALESCANC], [SALESFLAGS], [SALESREFUND], " \
               "[PACKNAME], [PACKCOUNT], [CASHIERID], [SALESATTRI], [SALESATTRS], [SALESEXTCOUNT], [DELFLAG], " \
               "[CLNTID], [SALESBONUS], [SYSTEMTYPE], [UPDATENUM]) " \
               "VALUES ("

        if level == 0:
            ins0 += " " + \
                    str(SALESNUM) + ',' + \
                    str(SESSID) + ',' + \
                    str(SYSTEMID) + ',' + \
                    str(SAREAID) + ',' + \
                    str(PRCLEVELID) + ',' + \
                    "NULL" + ',' + \
                    str(SALESTAG) + ',' + \
                    str(SALESTIME) + ',' + \
                    str(FRECNUM) + ',' + \
                    str(SRECNUM) + ',' + \
                    str(SALESBARC) + ',' + \
                    str(SALESDISC) + ',' + \
                    str(SALESPRICE) + ',' + \
                    str(SALESSUM) + ',' + \
                    str(BONUSSUM) + ',' + \
                    str(SALESCOUNT) + ',' + \
                    str(SALESCODE) + ',' + \
                    str(SALESTYPE) + ',' + \
                    str(SALESCANC) + ',' + \
                    str(SALESFLAGS) + ',' + \
                    str(SALESREFUND) + ',' + \
                    str(PACKNAME) + ',' + \
                    str(PACKCOUNT) + ',' + \
                    str(CASHIERID) + ',' + \
                    str(SALESATTRI) + ',' + \
                    str(SALESATTRS) + ',' + \
                    str(SALESEXTCOUNT) + ',' + \
                    str(DELFLAG) + ',' + \
                    str(CLNTID) + ',' + \
                    str(SALESBONUS) + ',' + \
                    str(SYSTEMTYPE) + ',' + \
                    str(UPDATENUM) + ')' + ';'
        if level == 1:
            ins0 += " " + \
                    str(SALESNUM) + ',' + \
                    str(SESSID) + ',' + \
                    str(SYSTEMID) + ',' + \
                    str(SAREAID) + ',' + \
                    str(PRCLEVELID) + ',' + \
                    "NULL" + ',' + \
                    str(SALESTAG) + ',' + \
                    str(SALESTIME) + ',' + \
                    str(FRECNUM) + ',' + \
                    str(SRECNUM) + ',' + \
                    str(SALESBARC) + ',' + \
                    "NULL" + ',' + \
                    "NULL" + ',' + \
                    str(SALESSUM) + ',' + \
                    "NULL" + ',' + \
                    str(SALESCOUNT) + ',' + \
                    "NULL" + ',' + \
                    str(SALESTYPE) + ',' + \
                    str(SALESCANC) + ',' + \
                    str(SALESFLAGS) + ',' + \
                    str(SALESREFUND) + ',' + \
                    str(PACKNAME) + ',' + \
                    "NULL" + ',' + \
                    str(CASHIERID) + ',' + \
                    "NULL" + ',' + \
                    str(SALESATTRS) + ',' + \
                    str(SALESEXTCOUNT) + ',' + \
                    str(DELFLAG) + ',' + \
                    str(CLNTID) + ',' + \
                    "NULL" + ',' + \
                    str(SYSTEMTYPE) + ',' + \
                    str(UPDATENUM) + ')' + ';'
        if level == 2:
            ins0 += " " + \
                    str(SALESNUM) + ',' + \
                    str(SESSID) + ',' + \
                    str(SYSTEMID) + ',' + \
                    str(SAREAID) + ',' + \
                    str(PRCLEVELID) + ',' + \
                    "NULL" + ',' + \
                    str(SALESTAG) + ',' + \
                    str(SALESTIME) + ',' + \
                    str(FRECNUM) + ',' + \
                    str(SRECNUM) + ',' + \
                    str(SALESBARC) + ',' + \
                    str(SALESDISC) + ',' + \
                    "NULL" + ',' + \
                    str(SALESSUM) + ',' + \
                    str(BONUSSUM) + ',' + \
                    str(SALESCOUNT) + ',' + \
                    "NULL" + ',' + \
                    "NULL" + ',' + \
                    str(SALESCANC) + ',' + \
                    str(SALESFLAGS) + ',' + \
                    str(SALESREFUND) + ',' + \
                    str(PACKNAME) + ',' + \
                    "NULL" + ',' + \
                    str(CASHIERID) + ',' + \
                    "NULL" + ',' + \
                    str(SALESATTRS) + ',' + \
                    str(SALESEXTCOUNT) + ',' + \
                    str(DELFLAG) + ',' + \
                    str(CLNTID) + ',' + \
                    str(SALESBONUS) + ',' + \
                    str(SYSTEMTYPE) + ',' + \
                    str(UPDATENUM) + ')' + ';'
        return ins0
    try:
        SALESTIME = '{0:%Y%m%d%H%M%S}'.format(datetime.datetime.now())
        DCARDCODE = cardCode
        ActualSalesCount = 1
        SALESTAG = 0
        SALESPRICE = ArtPrice
        SALESCOUNT = 1
        SALESSUM = SALESPRICE * SALESCOUNT
        SALESCODE = ArtCode
        SALESTYPE = 1
        PACKNAME = ArtPackId
        SALESEXTCOUNT = 0
        sql=""
        sql += MakeIns(0)
        SALESNUM += 1

        SALESTAG = 1
        SALESBARC = "'" + cardCode + ":'"
        SALESCOUNT = 1
        SALESTYPE = 6
        PACKNAME = "'Terminal'"
        SALESEXTCOUNT = 0

        sql += MakeIns(1)
        SALESNUM += 1
        SALESTAG = 2
        SALESBARC = "''"
        SALESCOUNT = 1

        sql += MakeIns(2)
        SALESNUM += 1

        GetDebitSql = "UPDATE ProcessingServer.dbo.ACCOUNTROOT " \
            "SET ACCOUNTSUM = ACCOUNTSUM - " + SALESSUM + " " \
            "WHERE clntid = " + clientId + " AND ISBLOCKED = 0 AND " \
            "ISCLOSED = 0 " \
            "AND ACCOUNTTYPEID = 3 AND CURRENCYID = 6;" \
            "UPDATE ProcessingServer.dbo.ACCOUNT " \
            "SET ACCOUNTSUM = ACCOUNTSUM - " + SALESSUM + " " \
            "WHERE clntid = " + clientId + " AND ISBLOCKED = 0 AND " \
            "ISCLOSED = 0 " \
            "AND ACCOUNTTYPEID = 3 AND CURRENCYID = 6;"

        updandins = "BEGIN TRAN; " + sql + GetDebitSql + "COMMIT TRAN;"
        cursor.execute(updandins)
        c.commit()
        time.sleep(1)
        line = str(cardCode) + " " + str(clientName) + " " + str(clientId) + " " + str(ArtCode) + " " + str(ArtPrice)
        writeLogBill(line)

        if ArtCode == Configuration.ArtCode1:
            pourCoffee(Configuration.Coffee1)
        elif ArtCode == Configuration.ArtCode2:
            pourCoffee(Configuration.Coffee2)
        elif ArtCode == Configuration.ArtCode3:
            pourCoffee(Configuration.Coffee3)
        elif ArtCode == Configuration.ArtCode4:
            pourCoffee(Configuration.Coffee4)
        c.close()

    except Exception as inst:
        writeLogError(inst)


class Char2Card:
    line = ""

    def __init__(self):

        def key_press(key):
            self.add2line(key.name)

        keyboard.on_press(key_press)
        while True:
            self.mi()

    def checkConnection(self):
        c = pymssql.connect(Configuration.IP, Configuration.User, Configuration.Password, "tempdb")
        cursor = c.cursor()
        test = "SELECT 1"
        cursor.execute(test)
        r = cursor.fetchone()
        if r[0] == 1:
            if Configuration.green_status_stop == False:
                statusOnline()
        else:
            statusOffline()
        c.close()

    def mi(self):
        while True:
            self.checkConnection()
            state5 = gpio.input(Configuration.Button5)
            while state5 == button_pressed:
                button5action()
                time.sleep(0.05)
            time.sleep(0.05)

    def add2line(self, a):
        if a != 'enter':
            self.line += a
        if a == "enter":
            #print(self.line)
            data = self.line
            self.clear()
            justDoIt(data)

    def clear(self):
        self.line = ""


init()
a = Char2Card()
