# **🏔** Swiss 3D

Swiss 3D delivers an easy way to create your custom 3D models (STL) from any part of switzerland. 

## Getting Started

### Hosted version

[Deployment on streamlit](https://swiss3d.streamlit.app/) with **grid resolution of 200m.**

As streamlit only provides 1GB space to host applications, please don't try to create to big models. **☠️**

### **Host locally**

Simply install python (I would recommend 3.12), create an environment and install the packages from the requirements.txt file. **🔮**

To start the application make sure your environment is active and run:

> streamlit run streamlit_app.py

## Change resolution to 25m:

As for the hosted version on streamlit resources are limited. 

But if you host the application locally you can further improve from a **25m grid resolution**. **💣**

To change the resolution from 200m to 25m just **modify line 66** in the **streamlit_app.py** to:

> st.session_state["sponsor"] = True


**Enjoy!**

[Buy me a coffee](https://buymeacoffee.com/schabi) [🙏](https://buymeacoffee.com/schabi)
