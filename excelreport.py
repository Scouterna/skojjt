# -*- coding: utf-8 -*-
import datetime
from openpyxl import Workbook, load_workbook
import io
from dakdata import DakData, Deltagare, Sammankomst

class ExcelReport:
	def __init__(self, dak, semester):
		self.dak = dak
		self.semester = semester

	def getFilledInExcelSpreadsheet(self):
		workbook = load_workbook("templates/narvarokort.xlsx")
		ws = workbook.worksheets[0]
		ws['E1'] = self.dak.kort.NaervarokortNummer
		ws['I1'] = self.semester.year
		ws['D2'] = self.dak.kort.NamnPaaKort
		ws['D3'] = self.dak.kort.Aktivitet
		ws['D4'] = self.dak.kort.Lokal
		if self.semester.ht:
			ws['E7'] = 'X'
		else:
			ws['C7'] = 'X'
		
		for index, sammankomst in enumerate(self.dak.kort.Sammankomster):
			if index > 37:
				ws['AU5'] = u"För många sammankomster" # TODO: fix multi page report
				break
			ws.cell(row=2, column=11+index).value = sammankomst.Aktivitet
			ws.cell(row=7, column=11+index).value = sammankomst.GetStartTimeString('%H')
			ws.cell(row=9, column=11+index).value = sammankomst.GetStopTimeString('%H')
			ws.cell(row=10, column=11+index).value = sammankomst.GetDateString('%m')
			ws.cell(row=11, column=11+index).value = sammankomst.GetDateString('%d')
			for deltagareindex, deltagare in enumerate(self.dak.kort.deltagare):
				if deltagare in sammankomst.deltagare:
					ws.cell(row=13+deltagareindex, column=11+index).value = 1

			for ledarindex, ledaren in enumerate(self.dak.kort.ledare):
				if ledaren in sammankomst.ledare:
					ws.cell(row=38+ledarindex, column=11+index).value = 1

		for index, deltagare in enumerate(self.dak.kort.deltagare):
			if index > 24:
				ws['AU6'] = u"För många deltagare" # TODO: fix multi page report
				break
			ws.cell(row=13+index, column=2).value = deltagare.Foernamn + " " + deltagare.Efternamn
			ws.cell(row=13+index, column=8).value = 'K' if deltagare.IsFemale() else 'M'
			ws.cell(row=13+index, column=9).value = deltagare.Postnummer
			ws.cell(row=13+index, column=10).value = deltagare.Personnummer[0:8]

		for index, ledaren in enumerate(self.dak.kort.ledare):
			if index > 2:
				ws['AU7'] = u"För många ledare" # TODO: fix multi page report
				break
			ws.cell(row=38+index, column=3).value = ledaren.Foernamn + " " + ledaren.Efternamn
			ws.cell(row=38+index, column=8).value = 'K' if ledaren.IsFemale() else 'M'
			ws.cell(row=38+index, column=9).value = ledaren.Postnummer
			ws.cell(row=38+index, column=10).value = ledaren.Personnummer[0:8]

		bytesIO = io.BytesIO()
		workbook.save(bytesIO)
		return bytesIO.getvalue()
