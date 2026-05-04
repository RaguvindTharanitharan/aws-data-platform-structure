// Command (Create layer) - node ..\build-scripts\initialize.js layer ../service_core/layers/python/service_core/
// Command (Remove layer) - node ..\build-scripts\initialize.js remove-layer ../service_core/layers
// Command (Create Glue Library) - node ..\build-scripts\initialize.js glue-library ../service_core/glue/service_core/ 1.0 demo-serverless /glueJobs/glue-libraries/ prod

const path = require('path');
const FileHelper = require('./file-helper.js');

const codeDirectories = [
  path.join(__dirname, "../service_core/repositories/"),
  path.join(__dirname, "../service_core/utils/"),
];

const skipLayerFiles = [
    // TODO: Add a list of file names that needs to be skipped as part of the layer build.
    "__init__.py",
    "athena_repository.py",
];

const skipGlueFiles = [
  // TODO: Add a list of file names that needs to be skipped as part of the glue library build.
  "__init__.py"
];

/**
 * Constructs a layer by creating necessary folders and copying files from the source directories to the destination directory.
 * 
 * This function performs the following steps:
 * 1. Creates the destination directory recursively if it doesn't exist.
 * 2. Iterates over each folder in the `layerDirectory`.
 * 3. Retrieves the list of files in each folder.
 * 4. Skips files that match any pattern in the `skipFiles` array.
 * 5. Copies each file from the source folder to the corresponding target folder in the destination directory.
 * 6. Logs a message for each skipped file.
 * 7. Logs a success message upon completion.
 * 8. Calls the `createInitializeFile` function after the layer is created.
 * 
 * @async
 * @function constructLayer
 * @returns {Promise<void>} A promise that resolves when the layer has been successfully created.
 */
async function constructLayer(skipFiles) {
  await FileHelper.createFolderRecursively(destinationDirectory);
  for (const folder of codeDirectories) {
    const files = await FileHelper.getFiles(folder);
    for (const file of files) {
      const sourceFile = path.join(folder, file);
      if (skipFiles.some(skipFile => file.includes(skipFile) || folder.includes(skipFile))) {
        console.log(`Skipped ${sourceFile}`);
        continue;
      }
      const targetFile = path.join(destinationDirectory, path.basename(folder), file);
      await FileHelper.createFolderRecursively(path.dirname(targetFile));
      await FileHelper.copyFile(sourceFile, targetFile);
    }
  }
  console.log('Layer created successfully!');
  await createInitializeFile();
}

/**
 * Asynchronously creates and initializes `__init__.py` files for all folders and files within a specified directory.
 * 
 * This function performs the following steps:
 * 1. Recursively retrieves all folders within the `destinationDirectory`.
 * 2. For each folder, it generates import statements for all Python files (excluding `__init__.py`).
 * 3. Writes the generated import statements to the `__init__.py` file within each folder.
 * 4. Creates a base `__init__.py` file in the `destinationDirectory` that imports all modules from all folders.
 * 
 * @async
 * @function createInitializeFile
 * @returns {Promise<void>} A promise that resolves when all `__init__.py` files have been created and written.
 */
async function createInitializeFile() {
  const folders = await FileHelper.getAllFoldersRecursively(destinationDirectory);
  let basedInitContent = "";
  let allContent = "\n__all__ = [";
  for (const folder of folders) {
    const folder_name = path.basename(folder);
    basedInitContent += `from .${folder_name} import `;
    const files = await FileHelper.getFiles(folder);
    let initContent = "";
    for (const file of files) {
      if (file === "__init__.py") {
        continue;
      }
      const fileName = path.basename(file, ".py");
      const splitFileName = fileName.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join('');
      initContent += `from .${fileName} import ${splitFileName}\n`;
      basedInitContent += `${splitFileName}, `;
      allContent += `'${splitFileName}', `;
    }
    const initFilePath = path.join(folder, "__init__.py");
    await FileHelper.writeFile(initFilePath, initContent);
    basedInitContent = basedInitContent.slice(0, -2) + "\n";
  }
  allContent = allContent.slice(0, -2) + "]\n";

  const initFilePath = path.join(destinationDirectory, "__init__.py");
  await FileHelper.writeFile(initFilePath, basedInitContent+allContent);
  console.log(allContent);
}

/**
 * Initializes the common library based on the specified mode.
 * 
 * Modes:
 * - 'layer': Constructs a layer.
 * - 'remove-layer': Removes a layer by deleting the destination directory.
 * 
 * @async
 * @function runInitialize
 * @throws Will throw an error if the mode is invalid.
 */
async function runInitialize() {
  console.log('Initializing common library...');
  if (mode === 'layer') {
    await constructLayer(skipLayerFiles);
  } else if (mode === 'glue-library') {
    await constructLayer(skipGlueFiles);
    zipFileLocation = `service_core_${version}.zip`
    await FileHelper.zipDirectory(path.dirname(destinationDirectory), zipFileLocation);
    console.log('Directory zipped successfully!');
  } else if (mode === 'remove-layer') {
    console.log('Removing layer...');
    await FileHelper.deleteFolderRecursively(destinationDirectory);
  } else if (mode === 'remove-file') {
    console.log('Removing file...');
    await FileHelper.deleteFile(destinationDirectory);
  }
  else {
    console.error(`Invalid mode: ${mode}`);
  }
}

const args = process.argv.slice(2);
const mode = args[0];
const destinationDirectory = args[1];
const version = args.length >= 3 ? args[2] : null;

// Validate command line arguments
if (!mode || !destinationDirectory) {
  console.error('Usage: node initialize.js <mode> <destination> [version]');
  console.error('Modes: layer, glue-library, remove-layer, remove-file');
  process.exit(1);
}

// Run initialization with error handling
(async () => {
  try {
    await runInitialize();
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
})();