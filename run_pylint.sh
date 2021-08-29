red=`tput setaf 1`
green=`tput setaf 2`
reset=`tput sgr0`

# Run pylint over all of the files
echo "${red}-----------------------------------${reset}"
echo "${red}-----------RUNNING PYLINT----------${reset}"
echo "${red}-----------------------------------${reset}"

echo "${red} Running pylint for all main files ${reset}"
echo "${green} run.py ${reset}"
pylint cortex/run.py
echo "${green} feature_types.py ${reset}"
pylint cortex/feature_types.py

echo "${red}----------------------------------${reset}"
echo "${red} Running pylint for all raw features ${reset}"
# TODO: add these
# echo "${green} gps.py ${reset}"
# pylint cortex/raw/gps.py

echo "${red}----------------------------------${reset}"
echo "${red} Running pylint for primary features ${reset}"
echo "${green} significant_locations.py ${reset}"
pylint cortex/primary/significant_locations.py
echo "${green} trips.py ${reset}"
pylint cortex/primary/trips.py
echo "${green} survey_scores.py ${reset}"
pylint cortex/primary/survey_scores.py
echo "${green} screen_active.py ${reset}"
pylint cortex/primary/screen_active.py
echo "${green} sleep_periods.py ${reset}"
pylint cortex/primary/sleep_periods.py

echo "${red}----------------------------------${reset}"
echo "${red} Running pylint for secondary features ${reset}"
# TODO: add these
echo "${green} entropy.py ${reset}"
pylint cortex/secondary/entropy.py
echo "${green} acc_jerk.py ${reset}"
pylint cortex/secondary/acc_jerk.py
echo "${green} hometime.py ${reset}"
pylint cortex/secondary/hometime.py
echo "${green} screen_duration.py ${reset}"
pylint cortex/secondary/screen_duration.py
echo "${green} call_duration.py ${reset}"
pylint cortex/secondary/call_duration.py

 echo "${reset}"