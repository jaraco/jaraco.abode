:tocdepth: 2

Supporting New Devices
======================

For new devices to be added to this library, the maintainers need the json values for each device. These values can be found by inspecting the network activity on the Abode webapp and pulling the data from the devices request or by using the CLI.

Getting Devices through Web App
-------------------------------

#. In a web browser, navigate to https://my.goabode.com/#/login
#. Open `Developer Tools <https://balsamiq.com/support/faqs/browserconsole/>`_
#. Click on "Network" to record network activity
#. Complete the login
#. Find "devices" under the Name column
#. Right click on the row and Copy -> Copy Response

Getting Devices through the CLI
-------------------------------

#. Follow the install directions
#. Run ``abode -u USERNAME -p PASSWORD --devices`` to get a list of devices
#. Run ``abode -u USERNAME -p PASSWORD --json DEVICE_ID`` with the device ID of the device of interest
#. Copy JSON data from the output

Remove identifying info (if applicable) and `create an issue <https://github.com/jaraco/jaraco.abode/issues/new>`_ with the data.
