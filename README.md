# R-Shiny-Survey-Creation-Automation-with-Selenium
Automates the Process of Creating Maxdiff Surveys on Qualtrics with R and Python. Users may upload a customs CSV list in the format of: Product, Number, and Image ID. 

Currently, Maxdiff Surveys on Qualtrics have to be manually created by hand each time, and there is no way to copy previous surveys. Tedious work, that requires precision and accuracy sounds like a perfect scenerio for Selenium for Web automation with Python. This Program will take in Username/Password, Main Survey Link (For redirecting at the end of the Maxdiff Survey), Number of Loops, and the Test variable. It'll: 
1. Login (Also featuring contigency Modal Dialogue for a Wrong Login), 
2. Create a new survey (Test Var Name + Current Iteration)
3. Import the features list from normal_features_list.csv
4. Select all the matching images from your company's library, assuming the image ID's are in normal_features_list.csv
5. Finishes the Advance tabs of the defining features options
6. Saves options and edits Survey Flow
7. Saves Survey Flow and beings next iteration

Please feel free to modify the program to suit your needs, most of the customization should easily be done in test_functions.py. Currently, a Dockerfile is provided to make it easier to host on Huggingface or another Shinyapp hosting site. 

When Modifying the program, please search (Ctrl + F) for '###' For notes on how to modify the program to suit your needs

It'll probably be helpful to let it run locally in headed mode for the first few runs until it is dialed in. As long as the main Features are being used in Maxdiff Surveys, and assuming your surveys follow the same pattern every time, this program will save you from some tedious work and minor headaches in the future
