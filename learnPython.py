from optparse import OptionParser

def main():
    optParser = OptionParser() 
    optParser.add_option('-f','--file',action = 'store',type = "string" ,dest = 'filename')
    optParser.add_option("-v","--vison", action="store_false", dest="verbose",
                          default='hello',help="make lots of noise [default]")
    #optParser.parse_args() 剖析并返回一个字典和列表，
    #字典中的关键字是我们所有的add_option()函数中的dest参数值，
    #而对应的value值，是add_option()函数中的default的参数或者是
    #由用户传入optParser.parse_args()的参数
    fakeArgs = ['-f','file.txt','-v','how are you', 'arg1', 'arg2']
    option , args = optParser.parse_args()
    op , ar = optParser.parse_args(fakeArgs)
    print("option : ",option)
    print("args : ",args)
    print("op : ",op)
    print("ar : ",ar)


if __name__ == '__main__':
    	main()
