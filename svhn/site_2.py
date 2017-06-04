import sys, os
from svhn import igan
from dataset import cook_split_inc as inc_dataset  
from yann.utils.pickle import load

if __name__ == '__main__':
    
    # simply locations
    gan = 39   # which epoch of gan do you want transfer to site 2 ?    
    site_1_root = 'records/site_1'
    root = 'records/site_2/gan_' + str(gan)
    data_loc = '/home/ASUAD/rvenka10/airlock'    
    if not os.path.exists(root):
        os.makedirs(root)           

    lr = (0.04, 0.001, 0.0001)    
    epochs =(30, 15)
    #p_vals = [0, 10, 50, 100, 500, 2000]
    p_vals = [ 5000, 10000, 25000]
    # p_vals = [ 35000, 45000, 60000]
    temperature = 3
    temp_data_params = {
               "source"             : 'matlab',
               # "name"               : 'yann_svhn', # some name.
               "location"     : data_loc,    # some location to load from.  
               "height"             : 32,
               "width"              : 32,
               "channels"           : 3,
               "batches2test"       : 2,
               "batches2train"      : 10,
               "mini_batches_per_batch" : (10, 10, 10),
               "batches2validate"   : 2,
               "mini_batch_size"    : 500}

    # setup incremental dataset parameters dataset.
    temp_splits = { "shot"               : [6,7,8,9],
                    "base"               : [0,1,2,3,4,5],    
                    "p"                  : 0   }  

    temp_base_data = inc_dataset (splits = temp_splits,
                                    data_params = temp_data_params,
                                  location = data_loc,
                                  verbose = 1)
    temp_base_data = temp_base_data.dataset_location()  
    site2 = igan ( init_dataset = temp_base_data, root = root, verbose = 1 )

    print (". Setup transfered gan network from site 1.")
    gan_params = load(site_1_root + '/resultor/gan/params/gan-5-31.pkl')
    site2.setup_gan(dataset = temp_base_data,
                    root = root, 
                    params = gan_params, 
                    cook = False,
                    verbose = 1)

    print (". Setup transfered base network from site 1.")    
    base_params = load(site_1_root + '/resultor/base-network/params/epoch_9.pkl') 
    site2.setup_base_mlp(   dataset = temp_base_data, 
                            root = root, 
                            params = base_params, 
                            cook = False,
                            verbose = 1)

    # setup incremental dataset parameters dataset.
    inc_splits = {  "base"               : [6,7,8,9],
                    "shot"               : [0,1,2,3,4,5],    
                    "p"                  : 0   }  

    for p in p_vals:
        
        inc_splits ['p'] = p 


        print (". Running p = " + str(p) )
        inc = inc_dataset (splits = inc_splits,
                           location = data_loc,            
                           verbose = 1)
        inc = inc.dataset_location()              

        # This will initialize the baseline incremental network.
        # This network is intended to demonstrate catastrophic forgetting
        # will be training with the increment dataset.
        if not os.path.exists (root + '/p_' + str(p)):
            os.makedirs(root + '/p_' + str(p))
        baseline_root = root + '/p_' + str(p) + '/baseline'
        site2.setup_baseline_inc ( dataset = inc, root = baseline_root, verbose = 1 )
        site2.train_baseline_inc ( lr =lr, epochs = epochs, verbose = 2 )

        # This will initialize and train the hallucinated incremental network.
        # This network is intended to deomonstrate that hallucinating from GAN 
        # could allow us to learn incremental learning. This is counter to 
        # what the baseline demonstrates.     
        igan_root = root + '/p_' + str(p) + '/igan'        
        site2.setup_mentor (temperature = temperature, verbose = 1)
        site2.setup_hallucinated_inc ( dataset = inc, root = igan_root, verbose = 1 )
        site2.train_hallucinated_inc ( lr =lr, epochs = epochs, verbose = 2 )            