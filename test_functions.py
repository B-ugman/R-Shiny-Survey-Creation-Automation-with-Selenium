import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

def create_webdriver():
  chrome_options = Options()
#  chrome_options.add_argument("--headless")  # Run in headless mode
  chrome_options.add_argument("--window-size=1920,1080")  # Set window size to 1920x1080
  # Create the WebDriver instance with options
  driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
  ## Webdriver wait
  wait = WebDriverWait(driver, 20)
  return driver, wait


def login_and_startup(driver, wait, user_login, pass_login):

    # Open the Qualtrics login page
    driver.get("https://qualtrics.com/login") ### Place your login page here. Example: https://qualtrics.com/login

    # Find the username field and enter the username
    username = driver.find_element(By.ID, "UserName")
    username.send_keys(user_login)

    # Find the password field and enter the password
    password = driver.find_element(By.ID, "UserPassword")
    password.send_keys(pass_login)

    # Find the login button and click it
    element = wait.until(EC.element_to_be_clickable((By.ID, "loginButton")))
    element.click()
    time.sleep(5)

### So this function creates the survey names. It works by taking the product name in the input box (The test variable) and adding Concept <Num> Maxdiff based on however many surveys you need
def create_survey(driver, wait, test_var, current_iteration):
    # Now find the button to create a new Survey
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='profile-data-create-new-button']")))
    element.click()

    # Now select maxdiff survey
    element = wait.until(EC.element_to_be_clickable((By.ID, 'GuidedProjects_ProductPrioritizationMaxDiff')))
    element.click()

    # Now select the 'Get started' button using CSS Selector
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='Catalog.DetailsPane.CallToAction']")))
    element.click()

    # Creating the Survey name variable with the current iteration
    survey_name = f"{test_var} - Concept {current_iteration} - Maxdiff"
    # Locate the textbox and paste the survey name from the input variable
    textbox_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='Catalog.GetStartedFlow.Name']")))
    textbox_element.send_keys(survey_name)

    max_retries = 3
    attempt = 0
    
    while attempt < max_retries:
        try:
            # Now click the 'Create project' button
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='Catalog.GetStartedFlow.Create']")))
            element.click()
            time.sleep(5)
            break  # Exit the loop if successful
        except Exception as e:
            attempt += 1
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print("Max retries reached. Giving up.")

### After creating a survey, this function defines the features of the maxdiff. This is where the Normal Features list csv file comes in to play. 
def define_features(driver, wait, test_var, features_list, current_iteration):
    # Clicking define features for MaxdiffSurvey
    # Wait for the button to be clickable and then click it
    time.sleep(2)
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='overview-step-define-features']")))
    element.click()

    # Now import the features based on the name of the concept being tested:
    # Click the 'import features' button
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='import-features-button']")))
    element.click()
    time.sleep(2)

    # Now paste into textbox the features and the survey concept being tested
    # Creating the test feature variable with the current iteration
    test_feature_name = f"{test_var} Concept {current_iteration}"
    features_list_full = features_list + [test_feature_name]
    features_string = ', '.join(features_list_full)

    # Now applying it to textbox
    textbox_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='copy-paste-attributes-input']")))
    textbox_element.send_keys(features_string)

    # Now wait a few seconds and click 'Import'
    time.sleep(0.5)
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='import-modal-import-button']")))
    element.click()
    time.sleep(3)



### My company always uses images with our Maxdiff Surveys, however, yours may be different
def add_images(driver, wait, beverages):
    for index, beverage in enumerate(beverages):
        feature = beverage.get('feature', '')
        testid = str(beverage.get('number', index))  # Ensure this is a string
        img_src = beverage.get('image_id', '')
        
        time.sleep(2)
        
        ## Add images to features in try block
        try:
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='add-image-{index}-button']")))
            element.click()
            time.sleep(2)
            
            # Select the dropdown menu
            element = wait.until(EC.element_to_be_clickable((By.ID, 'image-library-dropdown')))
            element.click()
            time.sleep(2)
            
            # Locate the dropdown element using a XPATH selector
            element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="image-library-dropdown-menu"]/div/div[3]')))
            element.click()
            
            # For the first image, wait 60 seconds. This tends to avoid overloading the Qualtrics Web API
            if index == 0:
                time.sleep(60)
            
            # Now find the image by ID
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'div > img[src*="{img_src}"]')))
            element.click()
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.upload-button")))
            element.click()
            time.sleep(2)
            
        except Exception as e:  ## I found the Qualtrics API is very spotty. This tries to avoid the program failing if the Images do not load.
            print(f"Failed to add image for {feature}: {e}")
            # Click Cancel and try again 1 time before moving on to next product
            try:
                element = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='button' and contains(@class, 'cancel-button') and not(contains(@data-testid, 'cancel-setup-button'))]")))
                element.click()
                print(f"Successfully clicked Cancel for {feature}")
            except Exception as cancel_e:
                print(f"Failed to click Cancel for {feature}: {cancel_e}")
            continue


### This function will probably need to be modified. It goes to the side tabs and changes some of the dialogue and number of features seen by each Survey respondent
def finish_features(driver, wait):
    time.sleep(2)
    # Click Display Tab
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='conjoint-overview-react']/div/div[1]/div[2]/a")))
    element.click()
    time.sleep(1)

    # Add the specified text to the first box
    input_xpath = "//*[@id='conjoint-overview-react']/div/div[2]/div/div[2]/label[1]/input"
    input_element = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
    input_element.send_keys(Keys.CONTROL, 'a')
    input_element.send_keys(Keys.BACK_SPACE)
    input_element.send_keys("From the products shown below, choose the one you would most prefer and least prefer purchasing.")
    time.sleep(1)

    # Move on to the 'Advanced' tab
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='conjoint-overview-react']/div/div[1]/div[3]/a")))
    element.click()
    time.sleep(1)

    # Set the Maxdiff questions per respondent to 6
    input_xpath = "//*[@id='conjoint-overview-react']/div/div[2]/div/div[2]/div[1]/label/input"
    input_element = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
    input_element.send_keys(Keys.CONTROL, 'a')
    input_element.send_keys(Keys.BACK_SPACE)
    input_element.send_keys("6")
    time.sleep(1)

    # Click the Anchored Maxdiff Question switch
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[data-testid='anchored-maxdiff-switch']")))
    element.click()
    time.sleep(1)



    ### You might want to change these depending on your company
    dialogues = {
        "all-important-input": "All of these are appealing",
        "some-important-input": "Some of these are appealing",
        "none-important-input": "None of these are appealing"
    }

    for input_id, text in dialogues.items():
        input_xpath = f"//*[@id='{input_id}']"
        input_element = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
        input_element.send_keys(Keys.CONTROL, 'a')
        input_element.send_keys(Keys.BACK_SPACE)
        input_element.send_keys(text)
        time.sleep(0.5)

    # Save the changes
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='save-setup-button']")))
    element.click()
    time.sleep(15)  # Wait for 60 seconds to ensure changes are saved





def survey_flow(driver, wait, current_iteration, extracted_string):
    time.sleep(10)
    # Navigate to the 'Survey' tab and then to 'Survey Flow'
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="gw-tab-SURVEY"]')))
    element.click()
    element = wait.until(EC.element_to_be_clickable((By.ID, "tab-button-surveyflow")))
    element.click()

    # Add Embedded Data fields
    ### This are highly specific to your surveys. I redacted mine, however, it'll probably help if you let it run once in headed mode, and see how exactly it runs before you modify it
    fields = ['Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example', 'Example']
    xpath_elements = ["//span[text()='Add a New Element Here']", "//*[@id='surveyflowembeddeddata']"]

    for xpath in xpath_elements:
        time.sleep(1)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        element.click()

    for field in fields:
        textbox_element = driver.find_element(By.ID, "InlineEditorElement")
        textbox_element.send_keys(field)
        textbox_element.send_keys(Keys.ENTER)

    # Set maxdiffconcept to the current concept being tested
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Flow"]/div[1]/div/div/div[7]/div/div[1]/div/div[1]/div[2]/div[1]/div/div[2]/div[8]/span')))
    element.click()

    ## This is annoying, but it requires a double click
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Flow"]/div[1]/div/div/div[7]/div/div[1]/div/div[1]/div[2]/div[1]/div/div[2]/div[8]/span')))
    element.click()
    textbox_element = driver.find_element(By.ID, "InlineEditorElement")
    textbox_element.clear()
    textbox_element.send_keys(str(current_iteration))

    # Add 'Show Block: Block 1' and 'Group Block: Do Not Delete 1'
    ## Now add a new 'Show Block: Block 1'
    ## First click 'Add element Label'
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.add-element-label')))
    element.click()

    ## Now click Showblock
    element = wait.until(EC.element_to_be_clickable((By.ID, 'surveyflowblock')))
    element.click()

    ## Now select the block options using the xpath
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Flow"]/div[1]/div/div/div[9]/div/div[1]/div/div[1]/div[2]/div[1]/div/select')))

    # Create a Select object
    select = Select(element)
    # Select the option with visible text 'Block 1'
    select.select_by_visible_text('Block 1')

    ## Now add a new 'Group Block: Do Not Delete 1'
    ## First click 'Add element Label'
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.add-element-label')))
    element.click()

    ## Now selecting Group box
    element = wait.until(EC.element_to_be_clickable((By.ID, "surveyflowgroup")))
    element.click()

    ## Now click the Untitled Group name to rename it
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Flow"]/div[1]/div/div/div[11]/div/div[1]/div/div[1]/div[2]/div[1]/div/span[2]/strong[2]')))
    element.click()

    # Search for the input field with the value "Untitled Group"
    input_xpath = '//input[@value="Untitled Group"]'
    input_element = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))

    ## Now selecting all in the textbox
    input_element.send_keys(Keys.CONTROL, 'a')
    input_element.send_keys(Keys.BACK_SPACE)
    input_element.send_keys("Do Not Delete")

    ## Now click 'Done'
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Flow"]/div[1]/div/div/div[11]/div/div[1]/div/div[1]/div[2]/div[1]/div/span[2]/span/a')))
    element.click()

    ## Now add a new element to the Do Not Delete Group just created
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Flow"]/div[1]/div/div/div[11]/div/div[3]/div/div[1]/div/div[1]/div/div[1]/div/div/a/span[2]')))
    element.click()

    ## Now selecting Embedded data box
    element = wait.until(EC.element_to_be_clickable((By.ID, "surveyflowembeddeddata")))
    element.click()

    ## Now naming this one 'mc'
    textbox_element = driver.find_element(By.ID, "InlineEditorElement")
    textbox_element.send_keys('mc')
    textbox_element.send_keys(Keys.ENTER)

    ## Now to set value of MC to 1
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Flow"]/div[1]/div/div/div[11]/div/div[3]/div/div[1]/div/div[1]/div[2]/div[1]/div/div[2]/div[1]/span')))
    element.click()

    ## Double clicking
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Flow"]/div[1]/div/div/div[11]/div/div[3]/div/div[1]/div/div[1]/div[2]/div[1]/div/div[2]/div[1]/span')))
    element.click()

    textbox_element = driver.find_element(By.ID, "InlineEditorElement")
    textbox_element.clear()
    textbox_element.send_keys("1")


    ## Now I need to click the first blank box and create the 'End of Survey' box
    ## First click Delete on Showblock1 at the top
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='Flow']/div[1]/div/div/div[3]/div/div[1]/div/div[1]/div[3]/a[4]")))
    element.click()

    ## Now clicking 'Ok' on the delete message
    ## Now selecting Embedded data box
    element = wait.until(EC.element_to_be_clickable((By.ID, "alertDialogOKButton")))
    element.click()


    ## Now to create end of survey block
    ## First click the bottom Add a New Element Box
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='Flow']/div[1]/div/div/div[11]/div/div[1]/div/div[1]/div/div[1]/div/div/a/span[2]")))
    element.click()

    ## Now selecting Embedded data box
    element = wait.until(EC.element_to_be_clickable((By.ID, "surveyflowendsurvey")))
    element.click()

    # Customize the End of Survey box with the modified link
    original_link = "https://ca1.qualtrics.com/jfe/form/<SURVEY_STRING>?P=2&V" ### Put any Main survey link here. It doesn't need to be modified ever again (Hopefully, since the User will input the current Survey link, and the program extracts the survey id and creates a new URL link), however, the SurveyID in the <SURVEY_STRING> will need to go in the next line
    modified_link = original_link.replace('<SURVEY_STRING>', extracted_string) ### 

    # Replace the specific part of the link
    modified_link = original_link.replace('<SURVEY_STRING>', extracted_string) ### Put the survey string to replace here as well

    ## Now with our modified link, we can Customize the End of Survey box
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='Flow']/div[1]/div/div/div[11]/div/div[1]/div/div[1]/div[3]/span/a")))
    element.click()

    ## Now select Override Survey Options
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='overrideOptions']")))
    element.click()

    ## Now Click Redirect to a URL
    element = wait.until(EC.element_to_be_clickable((By.ID, "SurveyTerminationRedirect")))
    element.click()


    ## Now input into the textbox the modified link we created
    textbox_element = driver.find_element(By.XPATH, "//*[@id='customizeContent']/div/div/input[4]")
    textbox_element.clear()
    textbox_element.send_keys(modified_link)

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[clickcallback='QSF_ElementView.customizeSave']")))
    element.click()

    ## Now apply and move back to the mains creen, and the program is complete
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='SurveyEditorContainer']/div[2]/div/div[3]/div[4]/div/button[2]")))
    element.click()


