

class MyClass:
	def __init__(self, a):
		self.a = a
	
	def setA(self, newA):
		self.a = newA

	def getA(self):
		return self.a

	def __str__(self):
		return self.a

t1 = MyClass('asdf')
t2 = MyClass('qwer')

lst = [t1, t2]

print([str(i) for i in lst])

t2.setA('pi')

print([str(i) for i in lst])

del t1

t3 = MyClass('asdf')

print(t3 in lst)

print([str(i) for i in lst])
