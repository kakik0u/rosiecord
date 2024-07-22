import os
import json
import logging
import shutil
import zipfile

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger()

# Define base directory
base_directory = os.getcwd()

# Check if a path exists
def path_exists(path):
    return os.path.exists(path)

# Rename .ipa to .zip and extract contents
def process_ipa_files():
    for file in os.listdir(base_directory):
        if file.endswith('.ipa'):
            ipa_path = os.path.join(base_directory, file)
            zip_path = ipa_path.replace('.ipa', '.zip')
            extract_dir = ipa_path.replace('.ipa', '')

            # Rename to .zip
            os.rename(ipa_path, zip_path)
            logger.info(f"Renamed {ipa_path} to {zip_path}")

            # Extract .zip contents
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            logger.info(f"Extracted {zip_path} to {extract_dir}")

            # Process the extracted directory
            process_extracted_directory(extract_dir)

            # Re-zip the contents
            shutil.make_archive(extract_dir, 'zip', extract_dir)
            logger.info(f"Re-zipped {extract_dir} to {extract_dir}.zip")

            # Rename back to .ipa
            os.rename(f"{extract_dir}.zip", ipa_path)
            logger.info(f"Renamed {extract_dir}.zip back to {ipa_path}")

            # Clean up extracted directory
            shutil.rmtree(extract_dir)
            logger.info(f"Cleaned up extracted directory {extract_dir}")

# Process the extracted directory
def process_extracted_directory(extract_dir):
    modules_path = os.path.join(extract_dir, 'Payload', 'Discord.app', 'assets', '_node_modules', '.pnpm')
    manifest_path = os.path.join(extract_dir, 'Payload', 'Discord.app', 'manifest.json')

    # Update manifest.json
    update_manifest(manifest_path)

    # Rename directories
    rename_directories(modules_path)

# Update manifest.json
def update_manifest(manifest_path):
    if not path_exists(manifest_path):
        logger.debug("Manifest file does not exist, no need to rename.")
        return

    with open(manifest_path, 'r', encoding='utf-8') as file:
        try:
            manifest = json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to unmarshal manifest.json. {e}")
            return

    if 'hashes' not in manifest:
        logger.info("No hashes found in manifest.json. Skipping React Navigation rename.")
        return

    # Change manifest hash path
    new_hashes = {}
    for key, value in manifest['hashes'].items():
        if '@react-navigation+elements' in key:
            logger.debug(f"Original key: {key}")
            split = key.split('/')

            for idx, segment in enumerate(split):
                if '@react-navigation+elements' in segment:
                    split[idx] = '@react-navigation+elements@patched'

            new_key = '/'.join(split)
            new_hashes[new_key] = value
            logger.debug(f"Updated key: {new_key}")
        else:
            new_hashes[key] = value

    manifest['hashes'] = new_hashes

    try:
        with open(manifest_path, 'w', encoding='utf-8') as file:
            json.dump(manifest, file, indent=2)
        logger.info("Wrote modified manifest.json file.")
    except IOError as e:
        logger.error(f"Failed to write modified manifest.json file. {e}")

# Rename directories
def rename_directories(modules_path):
    if not path_exists(modules_path):
        logger.debug("Node modules directory does not exist, no need to rename.")
        return

    try:
        directories = [d for d in os.listdir(modules_path) if '@react-navigation+elements' in d]
    except OSError as e:
        logger.error(f"Failed to read node_modules directory. Skipping React Navigation rename. {e}")
        return

    for directory in directories:
        current_name = os.path.join(modules_path, directory)
        new_name = os.path.join(modules_path, '@react-navigation+elements@patched')

        try:
            shutil.move(current_name, new_name)
            logger.info(f"Renamed React Navigation directory: {directory}")
        except OSError as e:
            logger.error(f"Failed to rename React Navigation directory: {directory} {e}")

    logger.info("Successfully renamed React Navigation directories.")

# Main function
def main():
    logger.debug("Starting the processing of .ipa files...")
    process_ipa_files()

if __name__ == "__main__":
    main()
