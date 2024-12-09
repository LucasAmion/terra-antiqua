Terra Antiqua
============================
This is a fork of Terra Antiqua plugin for QGIS, that adds two new features: the reconstruction of raster layers (Topography and Bathymetry) and the reconstruction of vector layers, using the **pyGPlates** library.

For the **Agegrid/Bathymetry** rasters, this plugin follows the workflow developed by Simon Williams et al. in their scientific article: ["Reconstructing seafloor age distributions in lost ocean basins"](https://doi.org/10.1016/j.gsf.2020.06.004). The associated code is available in the following repository: https://github.com/LucasAmion/agegrid.

Installation
====================
Some of the dependencies needed to run this plugin are only available through **conda**. This means that, if you have **QGIS** installed by other means, you are going to have to reinstall it through **conda**.

The process is as follows:

- First, you need to have **conda** installed in your system. It is recommended to install it from the [conda-forge distribution](https://conda-forge.org/download/), to ensure the **conda-forge** channel is available by default. If you installed conda via the Anaconda distribution instead, you need to enable the **conda-forge** channel manually by running the following command in your terminal:

  ```sh
  conda config --add channels conda-forge
  ```

  or adding the following lines to your `.condarc` file (commonly located in the user's home directory):

  ```yml
  channels:
  - conda-forge
  ```

- Secondly, you need to clone this repository into the directory where **QGIS** expects to find its plugins, namely `C:\Users\{USER}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins` in Windows and `/home/{USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins` in Linux.

  ```sh
  cd /home/{USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins
  git clone https://github.com/LucasAmion/terra-antiqua.git
  ```

  > **Note**: For this you git installed in your system. You can download it from here: https://git-scm.com/downloads. Alternatively, you can simply download the code of this repository as a ZIP file and extract it in the aforementioned directory.

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
