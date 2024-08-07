#!/bin/bash

beginswith() { case $2 in "$1"*) true;; *) false;; esac; }

# Set Timezone
export TZ="/usr/share/zoneinfo/$TZ"

echo "-------------------------------------------------------"
echo "Step 1: Waiting for Schema Registry to start listening "
echo "-------------------------------------------------------"
while [ $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) -eq 000 ] ; do
  echo -e $(date) " Registry listener HTTP state: " $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) " (waiting for 200)"
  sleep 5
done


echo "------------------------"
echo "Step 2: Creating Topics "
echo "------------------------"
create_topics


echo "---------------------------------------"
echo "Step 3: Adding Schemas to the registry "
echo "---------------------------------------"
create_schemas


echo "-------------------------"
echo "Step 4: Adding locations "
echo "-------------------------"
if [[ -z "${ALARM_LOCATIONS}" ]]; then
  echo "No locations specified"
elif beginswith 'https://' "${ALARM_LOCATIONS}"; then
  echo "HTTPS URL specified: $ALARM_LOCATIONS"
  wget -O /tmp/locations "$ALARM_LOCATIONS"
  set_location --file /tmp/locations
elif [[ -f "$ALARM_LOCATIONS" ]]; then
  echo "Attempting to setup locations from file $ALARM_LOCATIONS"
  set_location --file "$ALARM_LOCATIONS"
else
  echo "Attempting to setup locations"
  IFS=','
  read -a definitions <<< "$ALARM_LOCATIONS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      parent="${def[1]}"

      PARMS=("${name}")

      if [[  ! -z "${parent}" ]]; then
        PARMS+=(--parent "${parent}")
      fi

      set_location "${PARMS[@]}"
    done
fi


echo "--------------------------"
echo "Step 5: Adding categories "
echo "--------------------------"
if [[ -z "${ALARM_CATEGORIES}" ]]; then
  echo "No categories specified"
elif beginswith 'https://' "${ALARM_CATEGORIES}"; then
  echo "HTTPS URL specified: $ALARM_CATEGORIES"
  wget -O /tmp/categories "$ALARM_CATEGORIES"
  set_category --file /tmp/categories
elif [[ -f "$ALARM_CATEGORIES" ]]; then
  echo "Attempting to setup categories from file $ALARM_CATEGORIES"
  set_category --file "$ALARM_CATEGORIES"
else
  echo "Attempting to setup categories"
  IFS=','
  read -a definitions <<< "$ALARM_CATEGORIES"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      team="${def[1]}"

      PARMS=("${name}")

      if [[  ! -z "${team}" ]]; then
        PARMS+=(--team "${team}")
      fi

      set_category "${PARMS[@]}"
    done
fi


echo "-----------------------"
echo "Step 6: Adding classes "
echo "-----------------------"
if [[ -z "${ALARM_CLASSES}" ]]; then
  echo "No class definitions specified"
elif beginswith 'https://' "${ALARM_CLASSES}"; then
  echo "HTTPS URL specified: $ALARM_CLASSES"
  wget -O /tmp/classes "$ALARM_CLASSES"
  set_class --file /tmp/classes
elif [[ -f "$ALARM_CLASSES" ]]; then
  echo "Attempting to setup class definitions from file $ALARM_CLASSES"
  set_class --file "$ALARM_CLASSES"
else
  echo "Attempting to setup classes"
  IFS=','
  read -a definitions <<< "$ALARM_CLASSES"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      category="${def[1]}"
      priority="${def[2]}"
      rationale="${def[3]}"
      correctiveaction="${def[4]}"
      latchable="${def[5]}"
      filterable="${def[6]}"
      ondelayseconds="${def[7]}"
      offdelayseconds="${def[8]}"

      PARMS=("${name}" --category "${category}" --priority "${priority}" --rationale "${rationale}")
      PARMS+=(--correctiveaction "${correctiveaction}")

      if [[ "${latchable}" == "True" ]]; then
        PARMS+=(--latchable)
      else
        PARMS+=(--not-latchable)
      fi

      if [[ "${filterable}" == "True" ]]; then
        PARMS+=(--filterable)
      else
        PARMS+=(--not-filterable)
      fi

      if [[  ! -z "${ondelayseconds}" ]]; then
        PARMS+=(--ondelayseconds ${ondelayseconds})
      fi

      if [[  ! -z "${offdelayseconds}" ]]; then
        PARMS+=(--offdelayseconds ${offdelayseconds})
      fi

      set_class "${PARMS[@]}"
    done
fi


echo "-------------------------"
echo "Step 7: Adding instances "
echo "-------------------------"
if [[ -z "${ALARM_INSTANCES}" ]]; then
  echo "No alarm definitions specified"
elif beginswith 'https://' "${ALARM_INSTANCES}"; then
  echo "HTTPS URL specified: $ALARM_INSTANCES"

  if [[ -n "${ALARM_INSTANCES_URL_CSV}" ]]; then
    echo "Using URL_CSV: $ALARM_INSTANCES_URL_CSV"
    IFS=','
    read -a definitions <<< "$ALARM_INSTANCES_URL_CSV"
    for defStr in "${definitions[@]}";
      do
        echo "Loading URL: ${ALARM_INSTANCES}/${defStr}"
        wget -O /tmp/instances "${ALARM_INSTANCES}/${defStr}"
        set_instance --file /tmp/instances
      done
  else
    echo "Grabbing single URL"
    wget -O /tmp/instances "$ALARM_INSTANCES"
    set_instance --file /tmp/instances
  fi
elif [[ -f "$ALARM_INSTANCES" ]]; then
  echo "Attempting to setup alarm definitions from file $ALARM_INSTANCES"
  set_instance --file "$ALARM_INSTANCES"
else
  echo "Attempting to setup instances"
  IFS=','
  read -a definitions <<< "$ALARM_INSTANCES"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      class="${def[1]}"
      pv="${def[2]}"
      location="${def[3]}"
      maskedby="${def[4]}"
      screencommand="${def[5]}"

      PARMS=("${name}" --alarmclass "${class}" --location "${location}" --screencommand "${screencommand}")

      if [[ ! -z "${pv}" ]]; then
        PARMS+=(--pv "${pv}")
      fi

      if [[  ! -z "${maskedby}" ]]; then
        PARMS+=(--maskedby "${maskedby}")
      fi

      set_instance "${PARMS[@]}"
    done
fi

echo "-------------------------"
echo "Step 8: Adding overrides "
echo "-------------------------"
if [[ -z "${ALARM_OVERRIDES}" ]]; then
  echo "No override definitions specified"
elif beginswith 'https://' "${ALARM_OVERRIDES}"; then
  echo "HTTPS URL specified: $ALARM_OVERRIDES"
  wget -O /tmp/overrides "$ALARM_OVERRIDES"
  set_override --file /tmp/overrides
elif [[ -f "$ALARM_OVERRIDES" ]]; then
  echo "Attempting to setup class definitions from file $ALARM_OVERRIDES"
  set_override --file "$ALARM_OVERRIDES"
else
  echo "Non-file overrides from env not supported!"
fi

echo "---------------------"
echo "Step 9: Initialized! "
echo "---------------------"
touch /home/jaws/initialized

sleep infinity
