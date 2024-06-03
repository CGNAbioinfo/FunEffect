import sys
import os
import subprocess
import argparse

effectorP_directory= "/media/eduardo/D1/tools/EffectorP-3.0" 
predgpi_directory= "/media/eduardo/D1/tools/predgpi"
TMHMM2_directory= "/media/eduardo/D1/tools/tmhmm-2.0c"

def copy_file_to_folder(txt_file, out_folder):
    # Check if the text file exists
    if not os.path.exists(txt_file):
        print(f"Error: The file '{txt_file}' does not exist.")
        return
    
    # Check if the folder already exists
    if not os.path.exists(out_folder):
        # Create the folder if it doesn't exist
        os.makedirs(out_folder)
        print(f"Folder '{out_folder}' created successfully.")


    
    basename= txt_file.split("/")
    basename=basename[-1].split(".")
    final_dir = out_folder+"/"+basename[0]
    
    # Check if the folder already exists
    if not os.path.exists(final_dir):
        # Create the folder if it doesn't exist
        os.makedirs(final_dir)
        print(f"Folder '{final_dir}' created successfully.")

    
    # RUN signalP 5.0
    signalp_prefix = final_dir +"/"+ basename[0]
    signalP="signalp -fasta "+ txt_file +" -org euk -prefix "+ signalp_prefix
    os.system(signalP)
    signalP_output= signalp_prefix+"_summary.signalp5"
    list_signalP= final_dir+"/signalP_positive.txt"
    grep_signalP= "grep SP "+ signalP_output+" | cut -f 1| sort -u > " + list_signalP
    os.system(grep_signalP)

    # Extract fasta sequence of SignalP positive 
    signalP_fasta= final_dir+"/signalP_positive.faa"
    extract_fasta_signalP= "faSomeRecords "+ txt_file +" "+ list_signalP +" "+ signalP_fasta
    os.system(extract_fasta_signalP)
    
    # RUN WoLFP-SORT
    wolfPsort_out= final_dir+"/WolfPSort.out"
    wolfPsort= "runWolfPsortSummary fungi < "+ signalP_fasta + " > " + wolfPsort_out
    os.system(wolfPsort)
    wolfpsort_parse= "sed -i \'s/\\.1 /\\.1\\t/g\' "+ wolfPsort_out
    os.system(wolfpsort_parse)
    wolfpsort_parse_out=final_dir+"/signalP_positive.WolfPsort_positive.txt"
    wolfpsort_filter="grep 'extr [2][0-9]' "+ wolfPsort_out+ " | cut -f1 >  "+ wolfpsort_parse_out
    os.system(wolfpsort_filter)

    # Extract fasta usando WoLF-PSORT positive
    wolfpsort_fasta= final_dir+"/signalP_positive.WolfPsort_positive.faa"
    extract_fasta_wolfpsort= "faSomeRecords "+ txt_file +" "+ wolfpsort_parse_out +" "+ wolfpsort_fasta
    os.system(extract_fasta_wolfpsort)
    
    # RUN tmhmm
    os.chdir(final_dir)
    tmhmm_path = TMHMM2_directory+"/bin/decodeanhmm.Linux_x86_64"
    tmhmm_models = TMHMM2_directory+"/lib/TMHMM2.0.model"
    tmhmm_options = TMHMM2_directory+"/lib/TMHMM2.0.options"
    tmhmm_out =final_dir+"/signalP_positive.WolfPsort_positive.tmhh.out"
    tmhmm= "cat "+ wolfpsort_fasta + " | "+ tmhmm_path +" -f "+ tmhmm_options+" -modelfile "+ tmhmm_models+ " > " + tmhmm_out
    os.system(tmhmm)
    tmhmm_list= final_dir+"/tmHmm_positive.txt"
    tmhmm_filter= "sed \'s/\\.1.*/.1/\' "+ tmhmm_out +" | sed -z \'s/\\n%/\\t/g\' | grep \">\" | grep -w \'M\' | cut -f 1  | sed \'s/>//g\'  > "+  tmhmm_list
    os.system(tmhmm_filter)
    
    # RUN predGPI 
    predgpi_out= final_dir+"/"+basename[0]+"_predgpi.gff"
    predgpi_path=predgpi_directory+"/predgpi.py"
    predgpi= predgpi_path+ " -f "+ wolfpsort_fasta +" -o "+ predgpi_out + " -m gff3"
    os.system(predgpi)

    # Filter  tmhmm and predGPI outputs 
    merged_list= final_dir +"/tmHmm.positive_predgp.positive.txt"
    filter_predgpi= "grep 'GPI-anchor' "+ predgpi_out +" | cut -f1 | sed 's/\\.1.*/.1/g' | cat "+ tmhmm_list + " - | sort -u > "+ merged_list
    os.system(filter_predgpi)
    merged_list2= final_dir +"/signalP_positive.WolfPsort_positive.tmHmm_positive.predgpi_positive.txt"
    merge_thmm_predgpi="grep -vwf "+ merged_list +" "+ wolfpsort_parse_out +" > "+ merged_list2
    os.system(merge_thmm_predgpi)

    # Extract fasta of putative fungal effectors
    putative_effector_fasta= final_dir+"/signalP_positive.WolfPsort_positive.tmHmm_positive.predgpi_positive.faa"
    extract_fasta_putative_effector= "faSomeRecords "+ txt_file +" "+ merged_list2 +" "+ putative_effector_fasta
    os.system(extract_fasta_putative_effector)
    


    # RUN EffectorP 3.0 
    effectorP_path = effectorP_directory+"/EffectorP.py"
    effectorP_fasta = final_dir+"/"+basename[0]+"_effectors.fasta"
    effectorP_tab =  final_dir+"/"+basename[0]+"_effectors.tab"
    effectorP= "python "+ effectorP_path + " -f  -i " + putative_effector_fasta+ " -o "+ effectorP_tab + " -E " + effectorP_fasta
    os.system(effectorP)

    # Remove temporal temporal files
    rm = "rm *.faa *.txt *.gff *.out *.signalp5"
    os.system(rm)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run fungal effector prediction pipeline.")
    parser.add_argument("-i", "--input", help="Input fasta file", required=True)
    parser.add_argument("-o", "--output", help="Output directory", required=True)
    args = parser.parse_args()
    copy_file_to_folder(args.input, args.output)