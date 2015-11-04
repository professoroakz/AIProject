from matplotlib.pyplot import *
from numpy import *
import theano
import theano.printing as p
import theano.tensor as T
import gzip
import cPickle

def numpy_floatX(data):
    return asarray(data)


class SigmoidOutput():
    
    def __init__(self,n_in,n_out):
        init_var = .1
        self.W = theano.shared(init_var*random.randn(n_out,n_in))
        self.b = theano.shared(zeros(n_out))        
        self.params = [self.W, self.b] 

    def f_prop(self,h):
        return T.nnet.sigmoid(T.dot(self.W,h) + self.b)        
        
                        
class LinearOutput():
    
    def __init__(self,n_in,n_out):
        init_var = .1
        self.W = theano.shared(init_var*random.randn(n_out,n_in),name="W")
        self.b = theano.shared(zeros(n_out),name="b")        
        self.params = [self.W, self.b] 

    def f_prop(self,h):
        return T.dot(self.W,h) + self.b        
    
           
class LSTM_Pooled():
    
    def __init__(self,n_in,n_hid,n_out,output_type):
        
        self.lstm_layer = LSTM_Layer(n_in, n_hid, n_out)
        
        if output_type==0:
            self.outputLayer = SigmoidOutput(n_hid,n_out)
        else:
            self.outputLayer = LinearOutput(n_hid,n_out)
              
        W = self.outputLayer.params[0]
        b = self.outputLayer.params[1]
        
        self.params = self.lstm_layer.params +  [W ,b] 


    def apply(self,x):
        h = self.lstm_layer.apply(x)
        h_pooled = T.mean(h,axis = 0)
        
        y_hat = self.outputLayer.f_prop(h_pooled)
        return y_hat

    def apply_one_hot(self,x):
        h = self.lstm_layer.apply(x)
        h_pooled = T.mean(h,axis = 0)

        y_hat = self.outputLayer.f_prop(h_pooled)
        return y_hat

    def cost(self,x,y):
        y_hat = self.apply(x)
        C =  -T.mean(y * T.log(y_hat) + (1 - y)*T.log( (1 - y_hat)))
        return C
          
class LSTM_Layer():
    
    def __init__(self,n_in,n_hid,n_out):
        
        init_var = .1
        
        self.arc = [n_in,n_hid,n_out]
        
        #input
        self.Wi = theano.shared(init_var *random.randn(n_hid,n_in),name="Wi")
        self.Ui = theano.shared(init_var *random.randn(n_hid,n_hid),name="Ui")
        self.bi = theano.shared(zeros(n_hid),name="bi")
        
        #candidate value params
        self.Wc = theano.shared(init_var*random.randn(n_hid,n_in),name="Wc")
        self.Uc = theano.shared(init_var*random.randn(n_hid,n_hid),name="Uc")
        self.bc = theano.shared(zeros(n_hid),name="bc")
        
        #forget gate
        self.Wf = theano.shared(init_var*random.randn(n_hid,n_in),name="Wf")
        self.Uf = theano.shared(init_var*random.randn(n_hid,n_hid),name="Uf")
        self.bf = theano.shared(zeros(n_hid),name="bf")
        
        #output gate params
        self.W0 = theano.shared(init_var*random.randn(n_hid,n_in),name="W0")
        self.U0 = theano.shared(init_var*random.randn(n_hid,n_hid),name="U0")
        self.b0 = theano.shared(zeros(n_hid),name="b0")
        
        self.params = [self.Wi,self.Ui,self.bi,self.Wc,self.Uc,self.bc,self.Wf,self.Uf,self.bf,self.W0,self.U0,self.b0]

    def test(self):
        print "test test test"

    #treat X as a sequence of indexes to get around Theano's no sparse implementation
    def apply_one_hot(self,X):

        params = self.params
        def step(x,h,c_prev):

            Wi = params[0]
            Ui = params[1]
            bi = params[2]
            Wc = params[3]
            Uc = params[4]
            bc = params[5]
            Wf = params[6]
            Uf = params[7]
            bf = params[8]
            W0 = params[9]
            U0 = params[10]
            b0 = params[11]

            #i - open input gate
            i = T.nnet.sigmoid(Wi[x] + T.dot(Ui,h) + bi)

            #c- candidate value
            #c_t = T.tanh(T.dot(Wc,x) + T.dot(Uc,h) + bc)
            c_t = T.tanh(Wc[x] + T.dot(Uc,h) + bc)

            #forget gate
            #ft = T.nnet.sigmoid(T.dot(Wf,x) + T.dot(Uf,h) + bf)
            ft = T.nnet.sigmoid(Wf[x] + T.dot(Uf,h) + bf)

            c = i*c_t + ft*c_prev

            #output gate
            #ot = T.nnet.sigmoid(T.dot(W0,x) + T.dot(U0,h) + b0)
            ot = T.nnet.sigmoid(W0[x] + T.dot(U0,h) + b0)

            #hidden activation
            h_act = ot*T.nnet.sigmoid(c)

            return h_act,c


        #loop over data and make predictions
        n_samples = X.shape[0]

        #h0 = T.unbroadcast(T.as_tensor_variable(zeros([self.arc[1],1])),1)
        #c0 = T.unbroadcast(T.as_tensor_variable(zeros([self.arc[1],1])),1)

        h0 = theano.shared(zeros(self.arc[1]))
        c0 = theano.shared(zeros(self.arc[1]))

        [ch,H] = theano.scan(
                            fn = step,
                            sequences=X,
                            outputs_info=[h0,c0],
                            n_steps =n_samples
                    )

        #predicted y values
        h = ch[0]
        return h


    def apply(self,X):
        
        params = self.params
        def step(x,h,c_prev):
            
            Wi = params[0]
            Ui = params[1]
            bi = params[2]
            Wc = params[3]
            Uc = params[4]
            bc = params[5]
            Wf = params[6]
            Uf = params[7]
            bf = params[8]
            W0 = params[9]
            U0 = params[10]
            b0 = params[11]
        
            #i - open input gate
            i = T.nnet.sigmoid(T.dot(Wi,x) + T.dot(Ui,h) + bi)
            
            #c- candidate value
            c_t = T.tanh(T.dot(Wc,x) + T.dot(Uc,h) + bc)
            
            #forget gate
            ft = T.nnet.sigmoid(T.dot(Wf,x) + T.dot(Uf,h) + bf)
            
            c = i*c_t + ft*c_prev
            
            #output gate
            ot = T.nnet.sigmoid(T.dot(W0,x) + T.dot(U0,h) + b0)
            
            #hidden activation
            h_act = ot*T.nnet.sigmoid(c)       

            return h_act,c

        
        #loop over data and make predictions
        n_samples = X.shape[0]
    
        #h0 = T.unbroadcast(T.as_tensor_variable(zeros([self.arc[1],1])),1)
        #c0 = T.unbroadcast(T.as_tensor_variable(zeros([self.arc[1],1])),1)
        
        h0 = theano.shared(zeros(self.arc[1]))
        c0 = theano.shared(zeros(self.arc[1]))
        
        [ch,H] = theano.scan(
                            fn = step,
                            sequences=X,
                            outputs_info=[h0,c0],
                            n_steps =n_samples
                    )


        #predicted y values
        h = ch[0]
        return h

def gen_sine():
    
    
    learning_rate = 0.05
    n = 400
    X_data = sin(range(n)).reshape(n,1)
    X_data = zeros([n,2])
    for i in range(n):
        X_data[i,:] = [sin(i-1) , sin(i)]
    
    Y_value = sin(range(1,n+1)).reshape(n,1)
    lstm = LSTM(2,6,1,1)
    
    X = T.matrix('X')
    Y = T.matrix('Y')

    y_shape  = (Y.shape[0],1,1)
    cost = lstm.cost(X,Y)

    n_iters = 300
    params = lstm.params
    
    predict = theano.function(
            inputs = [X],
            outputs = [lstm.f_prop(X)]
        )
    
    params = lstm.params
    gparams = [T.grad(cost,param) for param in params]
    
    updates = [
        (param, param - learning_rate * gparam)
        for param, gparam in zip(params, gparams)
    ]

    train_model = theano.function(
            inputs = [X,Y],
            outputs = cost,
            updates=updates,    
        )
    
        
    
    for i in range(n_iters):
        print train_model(X_data,Y_value)
        
                              
                                                        
    y_hat = predict(X_data)[0].reshape(n,1)
    #print y_hat
    plot(Y_value)
    #print y_hat
    plot(y_hat,'r')
    show()                        
    
if __name__ == '__main__':
    
    gen_sine()
    