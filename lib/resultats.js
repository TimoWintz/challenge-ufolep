import fsPromises from 'fs/promises';
import path from 'path'

export async function getIndivData() {
    // Get the path of the json file
    const filePath = path.join(process.cwd(), 'data/resultats_indiv.json');
    // Read the json file
    const jsonData = await fsPromises.readFile(filePath);
    // Parse data as json
    const objectData = JSON.parse(jsonData);

    return objectData
}

export async function getClubData() {
    // Get the path of the json file
    const filePath = path.join(process.cwd(), 'data/resultats_club.json');
    // Read the json file
    const jsonData = await fsPromises.readFile(filePath);
    // Parse data as json
    const objectData = JSON.parse(jsonData);

    return objectData
}