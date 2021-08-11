from typing import TextIO
import VMCode as vm
import JackTokenizer as lexer

class VMCompileEngine:
    def __init__(self, fname):
        self.vm = vm.VMCode()
        self.jt = lexer.JackTokenizer(fname)
        
        self.op = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
        self.unaryOp = ['-', '~']

        self.tokenC = ''
        self.tokenT = ''
        self.className = ''


    def nextToken(self):
        if (self.jt.hasMoreTokens()):
            self.jt.advance()
            self.tokenC = self.jt.getToken()
            self.tokenT = self.jt.tokenType(self.tokenC)
    
    def esperado(self, token):
        if (self.tokenC == token):
            pass
        else:
            raise Exception('Valor Inesperado')

    def compile(self):
        self.nextToken()
        return self.compileClass()

    def compileClass(self):
    # compila uma classe completa
        self.esperado('class')
        self.nextToken() # tokenC = identificador da classe
        self.className = self.tokenC
        self.nextToken()
        self.esperado('{')
        self.nextToken()
        self.vm.nivel = True # nivel de classe
        self.compileClassVarDec()
        self.vm.nivel = False # Nivel de SubRoutine
        result = self.compileSubroutineDec()
        self.esperado('}')
        return result

    def compileClassVarDec(self):
    # compila uma variavel declarada STATIC ou declarada FIELD
        vars = ['field', 'static']
        
        if self.tokenC in vars:
            kind = self.tokenC
            self.nextToken()
            tipo = self.tokenC # type
            self.nextToken()
            name = self.tokenC # identificador
            self.nextToken()
            self.vm.define(name, tipo, kind)

            while (self.tokenC == ','):
                self.nextToken()
                name = self.tokenC # identificador
                self.nextToken()
                self.vm.define(name, tipo, kind)
            
            self.esperado(';')
            self.nextToken()
            self.compileVarDec()

    def compileSubroutineDec(self):
    # compila um metodo(METHOD), uma função(FUNCTION) ou um construtor(CONSTRUCTOR) completo
        result = ''
        subRoutines = ['constructor', 'function', 'method']

        if self.tokenC in subRoutines:
            self.vm.startSubRoutine()
            # tokenC = subRoutines
            self.nextToken() # tokenC = tipo
            self.nextToken()
            result += 'function ' + self.className + '.' + self.tokenC + '\n'# + ' ' + str(self.vm.indexOf(self.tokenC))
            self.nextToken()
            self.esperado('(')
            self.nextToken()
            self.compileParameterList()
            self.esperado(')')
            self.nextToken()
            result += self.compileSubroutineBody()
            result += self.compileSubroutineDec()

        return result
    
    def compileParameterList(self):
    # compila uma lista de parametros
        types = ['int', 'char', 'boolean', 'void']

        if (self.tokenC == ','):
            self.nextToken()
            self.compileParameterList()
        elif(self.tokenC in types):
            tipo = self.tokenC
            self.nextToken()
            name = self.tokenC
            self.vm.define(name, tipo, 'argument')
            self.compileParameterList()

    def compileSubroutineBody(self):
    # compila um corpo de subroutina
        self.esperado('{')
        self.nextToken()
        self.compileVarDec()
        result = self.compileStatements()
        self.esperado('}')
        self.nextToken()
        return result

    def compileVarDec(self):
    # compila uma declaração de variavel
        if (self.tokenC == 'var'):
            self.nextToken()
            tipo = self.tokenC # type
            self.nextToken()
            name = self.tokenC # identificador
            self.nextToken()
            self.vm.define(name, tipo, 'local')

            while (self.tokenC == ','):
                self.nextToken()
                name = self.tokenC # identificador
                self.nextToken()
                self.vm.define(name, tipo, 'local')
            
            self.esperado(';')
            self.nextToken()
            self.compileVarDec()

    def compileStatements(self):
    # compila uma sequencia de Statements
        result = ''

        if (self.tokenC == 'let'):
            result += self.compileLet()
            result += self.compileStatements()
        elif (self.tokenC == 'if'):
            result += self.compileIf()
            result += self.compileStatements()
        elif (self.tokenC == 'while'):
            result += self.compileWhile()
            result += self.compileStatements()
        elif (self.tokenC == 'do'):
            result += self.compileDo()
            result += self.compileStatements()
        elif (self.tokenC == 'return'):
            result += self.compileReturn()
            result += self.compileStatements()

        return result

    def compileLet(self):
    # compila um Statement Let
        result = ''

        self.nextToken() # tokenC = identificador
        id = self.tokenC
        self.nextToken()

        if (self.tokenC == '['):
            self.nextToken()
            result += self.compileExpression()
            self.esperado(']') # tokenC = ]
            self.nextToken()

        self.esperado('=') # tokenC = =
        self.nextToken()
        result += self.compileExpression()
        self.esperado(';') # tokenC = ;
        self.nextToken()

        result += self.vm.writePop(self.vm.kindOf(id), self.vm.indexOf(id))
        
        return result

    def compileIf(self):
    # compila um Statement If
        result = ''
        self.nextToken()

        label1 = 'IF_TRUE'
        label2 = 'IF_FALSE'
        label3 = 'IF_END'

        self.esperado('(')
        self.nextToken()
        result += self.compileExpression()
        self.esperado(')')
        self.nextToken()
        
        result += self.vm.writeIf(label1) # if-goto L1
        result += self.vm.writeGoto(label2) # goto L2
        result += self.vm.writeLabel(label1) # L1

        self.esperado('{')
        self.nextToken()
        result += self.compileStatements()
        self.esperado('}')
        self.nextToken()
        
        result += self.vm.writeGoto(label3) # goto END
        result += self.vm.writeLabel(label2) # L2

        self.esperado('else')
        self.nextToken()
        self.esperado('{')
        self.nextToken()
        result += self.compileStatements()
        self.esperado('}')
        self.nextToken()

        result += self.vm.writeLabel(label2) # L END

        return result

    def compileWhile(self):
    # compila um Statement While
        result = ''

        label1 = 'WHILE_EXP'
        label2 = 'WHILE_END'

        result += self.vm.writeLabel(label1) # L WHILE EXP

        self.nextToken()
        self.esperado('(')
        self.nextToken()
        result += self.compileExpression()
        self.esperado(')')

        result += self.vm.writeArithmetic('!')
        result += self.vm.writeIf(label2) # if-goto WHILE END

        self.nextToken()
        self.esperado('{')
        self.nextToken()
        result += self.compileStatements()
        self.esperado('}')
        self.nextToken()

        result += self.vm.writeGoto(label1) # goto WHILE EXP
        result += self.vm.writeLabel(label2) # L WHILE END

        return result

    def compileDo(self):
    # compila um Statement Do
        result = ''
        self.nextToken()
        # result += self.compileSubRoutineCall()
        result += self.esperado(';')
        self.nextToken()
        
        return result

    def compileReturn(self):
    # compila um Statement Return
        result = self.vm.writeReturn()
        self.nextToken()

        if (self.tokenC != ';'):
            result += self.compileExpression()
        else:
            self.nextToken()

        return result

    def compileExpression(self):
    # compila uma expressão
        result = self.compileTerm()

        while self.tokenC in self.op:
            op = self.tokenC
            self.nextToken()
            result += self.compileTerm()
            result += self.vm.writeArithmetic(op)

        return result

    def compileTerm(self):
        result = ''

        if (self.tokenT == 'integerConstant'):
            result += self.vm.writePush('constant', self.tokenC)
            self.nextToken()
        elif (self.tokenT == 'identifier'):
            id = self.tokenC
            self.nextToken()

            if (self.tokenC == '['):
                self.nextToken()
                result += self.compileExpression()
                self.nextToken()
            elif (self.tokenC == '(' or self.tokenC == '.'):
                result += self.compileSubroutineDec(id)
            else:
                result += self.vm.writePush(self.vm.kindOf(id), self.vm.indexOf(id))
        elif(self.tokenT == 'symbol'):
            if (self.tokenC == '('):
                self.nextToken()
                result += self.compileExpression()
                self.nextToken()
            elif (self.tokenC in self.unaryOp):
                unaryOP = self.tokenC
                self.nextToken()
                result += self.compileTerm()
                result += self.vm.writeArithmetic(unaryOP)

        return result

    def compileExpressionList(self):
    # compila uma lista de expressão
        if (self.tokenC == ')'):
            return ''
        else:
            result = self.compileExpression()

            if (self.tokenC == ','):
                self.nextToken()
                result += self.compileExpressionList()

            return result

test = VMCompileEngine("""// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/11/Average/Main.jack

// (Same as projects/09/Average/Main.jack)

// Inputs some numbers and computes their average
class Main {
   function void main() {
     var int i;
     
     let i = 0;
     while (i < 10) {
        let i = i + 1;
     }
     return;
   }
}""")
print(test.compile())