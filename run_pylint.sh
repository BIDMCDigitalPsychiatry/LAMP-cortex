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
echo "${red} Running pylint for visualization code ${reset}"
echo "${green} data_quality.py ${reset}"
pylint cortex/visualizations/data_quality.py
echo "${green} correlation_functions.py ${reset}"
pylint cortex/visualizations/correlation_functions.py

echo "${red}----------------------------------${reset}"
echo "${red} Running pylint for utils code ${reset}"
echo "${green} db.py ${reset}"
pylint cortex/utils/db.py
echo "${green} notifications.py ${reset}"
pylint cortex/utils/notifications.py
echo "${green} module_scheduler.py ${reset}"
pylint cortex/utils/module_scheduler.py
echo "${green} misc_functions.py ${reset}"
pylint cortex/utils/misc_functions.py
echo "${green} useful_functions.py ${reset}"
pylint cortex/utils/useful_functions.py

echo "${red}----------------------------------${reset}"
echo "${red} Running pylint for all raw features ${reset}"
echo "${green} accelerometer.py ${reset}"
pylint cortex/raw/accelerometer.py
echo "${green} analytics.py ${reset}"
pylint cortex/raw/analytics.py
echo "${green} balloon_risk.py ${reset}"
pylint cortex/raw/balloon_risk.py
echo "${green} bluetooth.py ${reset}"
pylint cortex/raw/bluetooth.py
echo "${green} calls.py ${reset}"
pylint cortex/raw/calls.py
echo "${green} cats_and_dogs.py ${reset}"
pylint cortex/raw/cats_and_dogs.py
echo "${green} device_state.py ${reset}"
pylint cortex/raw/device_state.py
echo "${green} device_motion.py ${reset}"
pylint cortex/raw/device_motion.py
echo "${green} gps.py ${reset}"
pylint cortex/raw/gps.py
echo "${green} gyroscope.py ${reset}"
pylint cortex/raw/gyroscope.py
echo "${green} jewels_a.py ${reset}"
pylint cortex/raw/jewels_a.py
echo "${green} jewels_b.py ${reset}"
pylint cortex/raw/jewels_b.py
echo "${green} nearby_device.py ${reset}"
pylint cortex/raw/nearby_device.py
echo "${green} pop_the_bubbles.py ${reset}"
pylint cortex/raw/pop_the_bubbles.py
echo "${green} screen_state.py ${reset}"
pylint cortex/raw/screen_state.py
echo "${green} sleep.py ${reset}"
pylint cortex/raw/sleep.py
echo "${green} sms.py ${reset}"
pylint cortex/raw/sms.py
echo "${green} spatial_span.py ${reset}"
pylint cortex/raw/spatial_span.py
echo "${green} steps.py ${reset}"
pylint cortex/raw/steps.py
echo "${green} survey.py ${reset}"
pylint cortex/raw/survey.py
echo "${green} telephony.py ${reset}"
pylint cortex/raw/telephony.py

echo "${red}----------------------------------${reset}"
echo "${red} Running pylint for primary features ${reset}"
echo "${green} acc_jerk.py ${reset}"
pylint cortex/primary/acc_jerk.py
echo "${green} game_level_scores.py ${reset}"
pylint cortex/primary/game_level_scores.py
echo "${green} screen_active.py ${reset}"
pylint cortex/primary/screen_active.py
echo "${green} significant_locations.py ${reset}"
pylint cortex/primary/significant_locations.py
echo "${green} survey_scores.py ${reset}"
pylint cortex/primary/survey_scores.py
echo "${green} trips.py ${reset}"
pylint cortex/primary/trips.py

echo "${red}----------------------------------${reset}"
echo "${red} Running pylint for secondary features ${reset}"
echo "${green} battery_level.py ${reset}"
pylint cortex/secondary/battery_level.py
echo "${green} call_degree.py ${reset}"
pylint cortex/secondary/call_degree.py
echo "${green} call_duration.py ${reset}"
pylint cortex/secondary/call_duration.py
echo "${green} call_number.py ${reset}"
pylint cortex/secondary/call_number.py
echo "${green} data_quality.py ${reset}"
pylint cortex/secondary/data_quality.py
echo "${green} entropy.py ${reset}"
pylint cortex/secondary/entropy.py
echo "${green} game_results.py ${reset}"
pylint cortex/secondary/game_results.py
echo "${green} healthkit_sleep_duration.py ${reset}"
pylint cortex/secondary/healthkit_sleep_duration.py
echo "${green} hometime.py ${reset}"
pylint cortex/secondary/hometime.py
echo "${green} inactive_duration.py ${reset}"
pylint cortex/secondary/inactive_duration.py
echo "${green} nearby_device_count.py ${reset}"
pylint cortex/secondary/nearby_device_count.py
echo "${green} screen_duration.py ${reset}"
pylint cortex/secondary/screen_duration.py
echo "${green} step_count.py ${reset}"
pylint cortex/secondary/step_count.py
echo "${green} survey_results.py ${reset}"
pylint cortex/secondary/survey_results.py
echo "${green} trip_duration.py ${reset}"
pylint cortex/secondary/trip_duration.py
echo "${green} trip_distance.py ${reset}"
pylint cortex/secondary/trip_distance.py

echo "${reset}"