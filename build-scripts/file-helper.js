const fs = require('fs');
const path = require('path');
const archiver = require('archiver');

/**
 * A helper class for file operations.
 */
class FileHelper {

  /**
   * Reads the content of a file at the given file path.
   * 
   * @param {string} filePath - The path to the file to be read.
   * @returns {Promise<string>} A promise that resolves with the file content as a string, or rejects with an error if the file cannot be read.
   */
  static async readFile(filePath) {
    return new Promise((resolve, reject) => {
      fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
          reject(err);
        } else {
          resolve(data);
        }
      });
    });
  }

  /**
   * Writes content to a file at the specified file path.
   *
   * @param {string} filePath - The path to the file where the content will be written.
   * @param {string} content - The content to write to the file.
   * @returns {Promise<void>} A promise that resolves when the file has been written successfully, or rejects with an error.
   */
  static async writeFile(filePath, content) {
    return new Promise((resolve, reject) => {
      fs.writeFile(filePath, content, 'utf8', (err) => {
        if (err) {
          reject(err);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Deletes a file at the specified file path.
   *
   * @param {string} filePath - The path to the file to be deleted.
   * @returns {Promise<void>} A promise that resolves when the file is successfully deleted, or rejects with an error if the deletion fails.
   */
  static async deleteFile(filePath) {
    return new Promise((resolve, reject) => {
      fs.unlink(filePath, (err) => {
        if (err) {
          reject(err);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Checks if a file exists at the given file path.
   *
   * @param {string} filePath - The path to the file to check.
   * @returns {Promise<boolean>} A promise that resolves to true if the file exists, otherwise false.
   */
  static async fileExists(filePath) {
    return new Promise((resolve) => {
      fs.access(filePath, fs.constants.F_OK, (err) => {
        resolve(!err);
      });
    });
  }

  /**
   * Extracts the file name from a given file path.
   *
   * @param {string} filePath - The full path of the file.
   * @returns {string} The name of the file.
   */
  static getFileName(filePath) {
    return path.basename(filePath);
  }

  /**
   * Retrieves the file extension from a given file path.
   *
   * @param {string} filePath - The path of the file.
   * @returns {string} The file extension, including the leading dot.
   */
  static getFileExtension(filePath) {
    return path.extname(filePath);
  }

  /**
   * Asynchronously creates a directory and any necessary subdirectories at the specified path.
   *
   * @param {string} folderPath - The path of the directory to create.
   * @returns {Promise<void>} - A promise that resolves when the directory is created.
   * @throws {Error} - Throws an error if the directory cannot be created.
   */
  static async createFolderRecursively(folderPath) {
    return new Promise((resolve, reject) => {
      fs.mkdir(folderPath, { recursive: true }, (err) => {
        if (err) {
          reject(err);
        } else {
          console.log(`Directory ${folderPath} created successfully!`);
          resolve();
        }
      });
    });
  }

  /**
   * Asynchronously retrieves the list of files in the specified folder.
   *
   * @param {string} folderPath - The path to the folder whose files are to be retrieved.
   * @returns {Promise<string[]>} A promise that resolves with an array of file names, or rejects with an error.
   */
  static async getFiles(folderPath) {
    return new Promise((resolve, reject) => {
      fs.readdir(folderPath, (err, files) => {
        if (err) {
          reject(err);
        } else {
          resolve(files);
        }
      });
    });
  }

  /**
   * Copies a file from the source path to the target path.
   *
   * @param {string} sourceFile - The path of the file to be copied.
   * @param {string} targetFile - The path where the file should be copied to.
   * @returns {Promise<void>} A promise that resolves when the file has been successfully copied.
   * @throws {Error} If an error occurs during the file copy operation.
   */
  static async copyFile(sourceFile, targetFile) {
    return new Promise((resolve, reject) => {
      fs.copyFile(sourceFile, targetFile, (err) => {
        if (err) {
          reject(err);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Recursively retrieves all folders within a given directory.
   *
   * @param {string} folderPath - The path of the folder to search within.
   * @returns {Promise<string[]>} A promise that resolves to an array of folder paths.
   */
  static async getAllFoldersRecursively(folderPath) {
    let folders = [];
    const items = await FileHelper.getFiles(folderPath);
    for (const item of items) {
      const fullPath = path.join(folderPath, item);
      const stats = fs.statSync(fullPath);
      if (stats.isDirectory()) {
        folders.push(fullPath);
        folders = folders.concat(await FileHelper.getAllFoldersRecursively(fullPath));
      }
    }
    return folders;
  }

  /**
   * Deletes a folder and its contents recursively.
   *
   * @param {string} folderPath - The path to the folder to be deleted.
   * @returns {Promise<void>} A promise that resolves when the folder is deleted successfully, or rejects with an error.
   */
  static async deleteFolderRecursively(folderPath) {
    return new Promise((resolve, reject) => {
      fs.rm(folderPath, { recursive: true, force: true }, (err) => {
        if (err) {
          reject(err);
        } else {
          console.log(`Directory ${folderPath} deleted successfully!`);
          resolve();
        }
      });
    });
  }

  /**
   * Asynchronously zips the contents of a directory.
   *
   * @param {string} source - The path to the directory to be zipped.
   * @param {string} out - The path where the output zip file will be written.
   * @returns {Promise<void>} A promise that resolves when the zipping is complete.
   * @throws {Error} If an error occurs during the zipping process.
   */
  static async zipDirectory(source, out) {
    const archive = archiver('zip', { zlib: { level: 9 } });
    const stream = fs.createWriteStream(out);

    return new Promise((resolve, reject) => {
      archive
        .directory(source, false)
        .on('error', err => reject(err))
        .pipe(stream);

      stream.on('close', () => resolve());
      archive.finalize();
    });
  }

  /***
   * delete a file at the specified file path
   */
  static async deleteFile(filePath) {
    return new Promise((resolve, reject) => {
      fs.unlink(filePath, (err) => {
        if (err) {
          reject(err);
        } else {
          resolve();
        }
      });
    });
  }
}

module.exports = FileHelper;