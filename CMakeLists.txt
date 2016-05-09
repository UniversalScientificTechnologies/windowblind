cmake_minimum_required(VERSION 2.8.3)
project(windowblind)


find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  message_generation
  genmsg
  actionlib_msgs
  actionlib
)


## Generate messages in the 'msg' folder
# add_message_files(
#   FILES
#   Message1.msg
#   Message2.msg
# )


## Generate services in the 'srv' folder
  add_service_files(
    FILES
    #MountGetCoordinates.srv
    #MountParameter.srv
    #RegisterDriver.srv
    #DriverControl.srv
    #NodeInfo.srv             # Pro ziskani informaci o nodech z AROM brain  -- servis 'arom/NodeInfo'
    PymlabInit.srv            # Pro inicializaci PYMLABU
    PymlabServerStatus.srv    # Pro
    PymlabDrive.srv           # Pro
  )

## Generate actions in the 'action' folder
# add_action_files(
#   FILES
#   Action1.action
#   Action2.action
# )

## Generate added messages and services with any dependencies listed here

  generate_messages(
    DEPENDENCIES
    actionlib_msgs
    std_msgs
  )

catkin_package(
   CATKIN_DEPENDS roscpp rospy std_msgs actionlib_msgs
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)