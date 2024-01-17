#!/usr/bin/env python
# coding: utf-8

# In[56]:


import numpy as np
import pandas as pd
from pymatgen.core import Structure
import matbench
import os
from matminer.datasets import load_dataset
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.analysis.structure_matcher import ElementComparator
from pymatgen.ext.matproj import MPRester
import shutil
import argparse

#In[121]:
compounds = ['LiF', 'NaF', 'KF', 'RbF', 'CsF', 'LiCl', 'NaCl', 'KCl', 'RbCl', 'CsCl',
            'BeO', 'MgO', 'CaO', 'SrO', 'BaO', 'ZnO', 'CdO', 'BeS', 'MgS', 'CaS', 'SrS',
            'BaS', 'ZnS', 'CdS', 'C', 'Si', 'GaAs', 'CdTe', 'CsPbI3',  'BN', 'GaN', 'ZrC',
            'SiC', 'WC', 'MnO', 'GaP', 'AlP', 'InP', 'LiBr', 'NaBr', 'KBr', 'RbBr', 'BeSe',
            'MgSe', 'CaSe', 'SrSe', 'BaSe']

#compounds = ['MgS']

parser = argparse.ArgumentParser()
parser.add_argument('--pdir', type = str, default = 'temp_folder')
parser.add_argument('--celltype', type = str, default = 'conventional')
args = parser.parse_args()

print('Geometry Optimization Run : {}'.format(args.pdir))
print('\n')

if args.celltype == 'primitive':
    unitcell_type = "cifs.primitive"
elif args.celltype == 'conventional':
    unitcell_type = "cifs.conventional_standard"

final_matching = {}
compounds_correctly_predicted = []
form_e_error_list = []
mape_lattice_list = []

for compound in compounds:
    path_to_crystal = '../results/{}'.format(compound)
    optimizer = 'tpe'
    pretty_formula = compound
    path_to_data = os.path.join(path_to_crystal, optimizer)

    MP_API_KEY = 'edSrcmMEuWF0k1Qi'
    properties = [unitcell_type, "formation_energy_per_atom"]
    criteria = {"formation_energy_per_atom": {"$exists": True}, "pretty_formula": pretty_formula}

    with MPRester(MP_API_KEY) as mpr:
        ground_truth = mpr.query(criteria, properties)

    #print(len(ground_truth))
    #print(ground_truth[0])
    
    # Updated Ground Truth (This is the only change from the original script crystal_matcher_folder.py)
    min_idx = 0
    for i in range(1, len(ground_truth)):
        if ground_truth[i]['formation_energy_per_atom'] < ground_truth[min_idx]['formation_energy_per_atom']:
            min_idx = i
    
    ground_truth = [ground_truth[min_idx]]
    
    #print(ground_truth)

    
    #all_directories = sorted(os.listdir(path_to_data))
    directory = compound + '_' + args.pdir
    path_to_curr_dir = os.path.join(path_to_data, directory)
    #print(path_to_curr_dir)

    energy_csv = pd.read_csv(path_to_curr_dir + '/results/energy_data.csv')
    min_energy = np.min(energy_csv['energy'])
    #print(min_energy)
    #print(energy_csv[energy_csv['energy'] == min_energy]['step'])
    optimal_step = int(energy_csv[energy_csv['energy'] == min_energy]['step'].iloc[0])


    best_cif = [x for x in os.listdir(path_to_curr_dir + '/results/structures/') if x.split('_')[-2] == str(optimal_step)]
    shutil.copy(path_to_curr_dir + '/results/structures/' + best_cif[0], path_to_curr_dir + '/results/structures/' + 'best_cif.cif')
    
    pred = Structure.from_file(path_to_curr_dir + '/results/structures/' + 'best_cif.cif')
    for i in range(len(ground_truth)):
        true = Structure.from_str(ground_truth[i][unitcell_type], fmt = 'cif')
        sm = StructureMatcher(comparator = ElementComparator(), primitive_cell = False)
        if sm.fit(pred, true) == True:
            true_form = ground_truth[i]['formation_energy_per_atom']
            form_e_error = abs(true_form - min_energy)
            lattice_pred = np.array([pred.as_dict()['lattice']['a'], pred.as_dict()['lattice']['b'],
                                    pred.as_dict()['lattice']['c']])
            lattice_true = np.array([true.as_dict()['lattice']['a'], true.as_dict()['lattice']['b'],
                                    true.as_dict()['lattice']['c']])
            mape_lattice = np.mean((np.abs(lattice_true - lattice_pred) / lattice_true) * 100)
            if mape_lattice < 25:
                final_matching[directory.split('_')[0]] = [True, form_e_error, mape_lattice]
                compounds_correctly_predicted.append(directory.split('_')[0])
                form_e_error_list.append(form_e_error)
                mape_lattice_list.append(mape_lattice)
            break


# In[127]:


print(final_matching)
print('\n')
print('Number of correctly predicted structures : {}'.format(len(compounds_correctly_predicted)))
print('MAE in formation energy for correctly predicted structures : {} meV/atom'.format(round(np.mean(form_e_error_list)*1000, 3)))
print('MAPE in predicted lattice length for correctly predicted structures : {}%'.format(round(np.mean(mape_lattice_list), 3)))

# In[128]:


#Structure.from_str(ground_truth[i]['cifs.conventional_standard'], fmt = 'cif').as_dict()['lattice']['a']


# In[129]:


#mean_form_error = np.mean([final_matching[x][1] for x in final_matching])
#mean_lattice_percent_error = np.mean([final_matching[x][2] for x in final_matching])


# In[130]:


#print('Mean Absolute Error in Prediction of Formation Energy is {} eV/atom'.format(round(mean_form_error, 4)))
#print('Mean Absolute Percentage Error in Prediction of Lattice Constant is {}%'.format(round(mean_lattice_percent_error, 3)))


# In[ ]:




