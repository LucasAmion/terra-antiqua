# Terra Antiqua
This is a fork of Terra Antiqua plugin for QGIS, that adds two new features: the reconstruction of raster layers (Topography and Bathymetry) and the reconstruction of vector layers, using the **pyGPlates** library.

For the **Agegrid/Bathymetry** rasters, this plugin follows the workflow developed by Simon Williams et al. in their scientific article: ["Reconstructing seafloor age distributions in lost ocean basins"](https://doi.org/10.1016/j.gsf.2020.06.004). The associated code is available in the following repository: https://github.com/LucasAmion/agegrid.

## Installation
There are two main ways to install this plugin depending on your platform:

### Windows
- The first step is to install QGIS. In Windows you can use the official OSGeo installer available at https://qgis.org/download/.

- Before installing the plugin, it is necesary to have [GMT (Generic Mapping Tools)](https://www.generic-mapping-tools.org/) available in your system, as it is used in the Bathymetry reconstruction feature. This can be done by running `winget install gmt6` or by downloading and running the appropriate installer from GMT's Github repository: https://github.com/GenericMappingTools/gmt/releases/latest

- Once installed, you'll need to add the GMT executable to QGIS's path varible so that it can be found. For this you have to go to **Settings -> Options -> System -> Environment** and check the *"Use custom variables"* option, click the *"+"* sign to add a new variable and enter the following values: **Apply = Append, Variable = Path, Value = ;C:\programs\gmt6\bin** (C:\programs\gmt6\bin is the default location but this can be modified during the installation process, make sure to choose the correct value). Then, restart QGIS to apply the changes.

![path-variable](https://github.com/user-attachments/assets/dee8e3d8-de49-458f-85b3-74a725815873)

- To install the plugin you can download this repository as a .zip file by clicking on Code -> Download as ZIP.

![download-zip](https://github.com/user-attachments/assets/f1504254-94ae-4c5b-beb0-f56a3d7200bf)

- Once in the QGIS interface, install the plugin by going to **Plugins -> Manage and install plugins -> Install from ZIP** and choose the .zip already downloaded.

![install-zip](https://github.com/user-attachments/assets/daf2a506-6379-4eae-82ac-fa7bc65c3b23)

- Finally, activate the plugin by ticking the corresponding checkbox in the installed plugins list. The first time the plugin is loaded, all the necesary python dependecies will be automatically installed.

### Conda

For other platforms such as Linux the recommend instalation method is through conda. The process is as follows:

- First, you need to have **conda** installed in your system. This can be done through [miniconda](https://www.anaconda.com/download/success) or [miniforge](https://conda-forge.org/download/).

- Secondly, you need to clone this repository into the directory where **QGIS** expects to find its plugins which is `/home/{USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins` in Linux.

  ```sh
  mkdir -p /home/{USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins
  cd /home/{USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins
  git clone https://github.com/LucasAmion/terra-antiqua.git
  ```

  > **Note**: For this you git installed in your system. Alternatively, you can simply download the code of this repository as a ZIP file and extract it in the aforementioned directory.

- Finally, install all the necessary conda dependencies (listed in the `environment.yml` file) by running the following command while inside the root folder of the project:

  ```sh
  cd terra-antiqua
  conda env create -n terra antiqua
  ```

  This will create a new conda environment called `terra-antiqua` with all the necessary dependencies including **GPlates** and **QGIS** itself.

Now, to use the software you just need to activate the environment and run **QGIS** like so:

```sh
conda activate terra-antiqua
qgis
```

If instead you wish to install the dependencies in an already existing conda environment you need to activate said environment and run this command:

```sh
conda env update --file environment.yml
```
