import "dotenv/config";
import { Connection, Keypair, PublicKey, clusterApiUrl } from "@solana/web3.js";
import { createMint, getOrCreateAssociatedTokenAccount, mintTo } from "@solana/spl-token";

const [userWallet, name, description] = process.argv.slice(2);

if (!userWallet || !name) {
    console.log(JSON.stringify({
        mint_address: null,
        error: "Usage: node mint_nft.js <USER_WALLET> <NAME> [DESCRIPTION]"
    }));
    process.exit(1);
}

const secretKey = JSON.parse(process.env.MASTER_WALLET_SECRET);
const masterKeypair = Keypair.fromSecretKey(Uint8Array.from(secretKey));

const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

async function mintNFT() {
    try {
        const mint = await createMint(
            connection,
            masterKeypair,
            masterKeypair.publicKey,
            null,
            0
        );

        const userToken = await getOrCreateAssociatedTokenAccount(
            connection,
            masterKeypair,
            mint,
            new PublicKey(userWallet)
        );

        await mintTo(
            connection,
            masterKeypair,
            mint,
            userToken.address,
            masterKeypair,
            1
        );

        console.log(JSON.stringify({ mint_address: mint.toBase58() }));
    } catch (err) {
        console.log(JSON.stringify({ mint_address: null, error: err.message }));
    }
}

mintNFT();
