library(shiny)
library(readr)
library(reticulate)

# Source the Python functions
source_python("test_functions.py")

ui <- fluidPage(
  titlePanel("Qualtrics Survey Creation App"),
  
  sidebarLayout(
    sidebarPanel(
      textInput("user_login", "Username:"),
      passwordInput("pass_login", "Password:"),
      textInput("test_var", "Test Variable:"),
      numericInput("num_loops", "Number of Loops:", value = 1, min = 1),
      textInput("url", "Master URL:"),
      fileInput("custom_features", "Upload Custom Features CSV (optional)", accept = ".csv"),
      actionButton("run_script", "Run Script"),
      actionButton("refresh", "Refresh App")
    ),
    
    mainPanel(
      verbatimTextOutput("status_output")
    )
  )
)

server <- function(input, output, session) {
  # Reactive values for driver, wait, login status, and credentials
  rv <- reactiveValues(
    driver = NULL, 
    wait = NULL, 
    login_successful = FALSE,
    username = "",
    password = ""
  )
  
  # Notification IDs
  notification_ids <- reactiveVal(character(0))
  
  # Function to show task notifications
  show_task_notification <- function(task_name, action, type = "default") {
    timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
    message <- sprintf("[%s] %s: %s", timestamp, action, task_name)
    id <- showNotification(message, type = type, duration = NULL)
    notification_ids(c(notification_ids(), id))
  }
  
  # Function to clear notifications
  clear_notifications <- function() {
    for (id in notification_ids()) {
      removeNotification(id)
    }
    notification_ids(character(0))
  }
  
  # Function to show login modal
  show_login_modal <- function() {
    showModal(modalDialog(
      title = "Login Failed",
      textInput("modal_username", "Username", value = rv$username),
      passwordInput("modal_password", "Password"),
      footer = tagList(
        modalButton("Cancel"),
        actionButton("modal_login", "Login")
      )
    ))
  }
  
  # Function to attempt login
  attempt_login <- function(username, password) {
    show_task_notification("Login", "Starting")
    tryCatch({
      if (is.null(rv$driver)) {
        driver_wait <- create_webdriver()
        rv$driver <- driver_wait[[1]]
        rv$wait <- driver_wait[[2]]
      }
      login_and_startup(rv$driver, rv$wait, username, password)
      Sys.sleep(5)  # Wait for page to load
      current_url <- rv$driver$current_url
      show_task_notification("Login", "Completed")
      
      if (current_url == "https://qualtrics.com/login") { ### Please make sure this is the same login page as you put in the test_functions.py. This checks to see if the User is stuck on a loginpage (Likely due to a wrong username/password) and prompts a Modal dialogue for new credentials
        FALSE  # Login failed 
      } else {
        rv$username <- username
        rv$password <- password
        TRUE   # Login successful
      }
    }, error = function(e) {
      show_task_notification("Login", "Failed", type = "error")
      showNotification(paste("Login error:", e$message), type = "error")
      FALSE
    })
  }
  
  # Function to read features data
  read_features_data <- reactive({
    if (!is.null(input$custom_features)) {
      read_csv(input$custom_features$datapath)
    } else {
      read_csv("normal_features_list.csv") ### So this is the default features list. It's a csv file of feature (text data), number (int), image_id (text data)
    } ### The image id is what you get when you inspect element on the pictures in the Qualtrics User library. I included an example Id, but make sure it works in headed mode before switching to headless
      ### The image feature isn't a requirement in the script, and you can choose to remove it for your purposes. It'll move on to the finishing features in Qualtrics
  })
  
  # Function to run a single iteration of the main script
  run_single_iteration <- function(current_iteration, extracted_string, features_list, beverages) {
    # Clear notifications before each new iteration
    clear_notifications()
    
    # Show what iteration we are on
    showNotification(sprintf("Starting iteration %d of %d", current_iteration, input$num_loops), type = "message", duration = NULL)
    
    tryCatch({ ### Qualtrics tends to break after the first loop, so modified the program to make it where the old webdriver is killed and a fresh one is created for every loop.
      # Create new driver and login
      driver_wait <- create_webdriver()
      rv$driver <- driver_wait[[1]]
      rv$wait <- driver_wait[[2]]
      
      login_successful <- attempt_login(rv$username, rv$password)
      if (!login_successful) {
        show_login_modal()
        return(FALSE)
      }
      
      # Start creating survey
      show_task_notification("Create Survey", "Starting")
      create_survey(rv$driver, rv$wait, input$test_var, current_iteration)
      show_task_notification("Create Survey", "Completed")
      
      # Now get the url for later
      previous_url <- rv$driver$current_url
      print(paste("Current URL:", previous_url))
      
      # Define Features of Survey
      show_task_notification("Define Features", "Starting")
      define_features(rv$driver, rv$wait, input$test_var, features_list, current_iteration)
      show_task_notification("Define Features", "Completed")
      
      # Add images to Survey
      show_task_notification("Add Images", "Starting")
      add_images(rv$driver, rv$wait, beverages)
      show_task_notification("Add Images", "Completed")
      
      # Finish the Features of Survey
      show_task_notification("Finish Features", "Starting")
      finish_features(rv$driver, rv$wait)
      show_task_notification("Finish Features", "Completed")
      
      ## Incase the features take too long to finish, then we can add an extra 30 second wait to avoid loop failure
      # Now get the url for later

      # Get the current URL
      current_url <- rv$driver$current_url
      print(paste("Current URL:", current_url))
      
      # Check if the current URL matches the previous URL
      if (!is.null(previous_url) && current_url != previous_url) {
        show_task_notification("Driver not yet at Maxdiff homepage", "Error Might Occur")
        print("Driver not at Maxdiff Survey homepage. Sleeping for 30 seconds... ")
        Sys.sleep(30)
      }
      
      # Configure Survey Flow
      show_task_notification("Configure Survey Flow", "Starting")
      survey_flow(rv$driver, rv$wait, current_iteration, extracted_string)
      show_task_notification("Configure Survey Flow", "Completed")
      
      return(TRUE)
    }, error = function(e) {
      showNotification(sprintf("Error in iteration %d: %s", current_iteration, e$message), type = "error", duration = NULL)
      return(FALSE)
    }, finally = {
      # Close the driver
      show_task_notification("Closing Driver", "Starting")
      if (!is.null(rv$driver)) {
        tryCatch({
          rv$driver$quit()
        }, error = function(e) {
          showNotification(sprintf("Error closing driver: %s", e$message), type = "warning", duration = NULL)
        })
      }
      rv$driver <- NULL
      rv$wait <- NULL
      show_task_notification("Closing Driver", "Completed")
    })
  }
  
  ## Loops function
  # Function to run the main script
  run_main_script <- function() {
    withProgress(message = 'Running script', value = 0, {
      tryCatch({
        # Extract the survey ID using R's regex functions
        extracted_string <- sub("survey-builder/", "", regmatches(input$url, regexpr("survey-builder/([^/]+)", input$url)))
        
        # Read features data
        features_data <- read_features_data()
        
        # Convert features_data to a list to pass to Python
        features_list <- as.list(features_data$feature)
        beverages <- lapply(1:nrow(features_data), function(i) {
          list(
            feature = features_data$feature[i],
            number = as.character(features_data$number[i]),  # Ensure this is a character
            image_id = features_data$image_id[i]
          )
        })
        
        
        
        # Run iterations
        for (i in seq_len(input$num_loops)) {
          iteration_success <- run_single_iteration(i, extracted_string, features_list, beverages)
          if (!iteration_success) {
            showNotification(sprintf("Iteration %d failed. Moving to next iteration.", i), type = "warning", duration = NULL)
          }
          incProgress(1/input$num_loops)
        }
        
        showNotification("Process completed. Check individual iteration results.", type = "message", duration = NULL)
      }, error = function(e) {
        showNotification(sprintf("An error occurred in the main script: %s", e$message), type = "error", duration = NULL)
      })
    })
  }
  ##
  
  # Handle login button in modal
  observeEvent(input$modal_login, {
    removeModal()
    rv$login_successful <- attempt_login(input$modal_username, input$modal_password)
    if (!rv$login_successful) {
      show_login_modal()
    } else {
      showNotification("Login successful!", type = "message")
      run_main_script()
    }
  })
  
  # Run script on button click
  observeEvent(input$run_script, {
    clear_notifications()
    rv$username <- input$user_login
    rv$password <- input$pass_login
    rv$login_successful <- attempt_login(rv$username, rv$password)
    if (!rv$login_successful) {
      show_login_modal()
    } else {
      showNotification("Login successful! Proceeding with the script.", type = "message")
      run_main_script()
    }
  })
  
  # Refresh function
  refresh_app <- function() {
    if (!is.null(rv$driver) && !is.null(rv$driver$session_id)) {
      show_task_notification("Refresh", "Killing driver")
      tryCatch({
        rv$driver$quit()
      }, error = function(e) {
        # Ignore any errors related to quitting the driver
      })
    }
    
    rv$driver <- NULL
    rv$wait <- NULL
    rv$login_successful <- FALSE
    rv$username <- ""
    rv$password <- ""
    
    show_task_notification("Refresh", "Reloading Python functions")
    reticulate::source_python("test_functions.py")
    
    updateTextInput(session, "user_login", value = "")
    updateTextInput(session, "pass_login", value = "")
    updateTextInput(session, "test_var", value = "")
    updateNumericInput(session, "num_loops", value = 1)
    updateTextInput(session, "url", value = "")
    
    showNotification("App refreshed successfully!", type = "message")
  }
  
  # Refresh button event handler
  observeEvent(input$refresh, {
    refresh_app()
  })
  
  # Handle session end
  session$onSessionEnded(function() {
    if (!is.null(rv$driver) && !is.null(rv$driver$session_id)) {
      tryCatch({
        rv$driver$quit()
      }, error = function(e) {
        # Ignore any errors related to quitting the driver
      })
    }
  })
}

shinyApp(ui, server)

















