import "dotenv/config";
import { Connection, Keypair, PublicKey, clusterApiUrl } from "@solana/web3.js";
import { getOrCreateAssociatedTokenAccount, transfer } from "@solana/spl-token";

const [userWallet] = process.argv.slice(2);

if (!userWallet) {
    console.log(JSON.stringify({ success: false, error: "Usage: node transfer_loyalty_token.js <USER_WALLET>" }));
    process.exit(1);
}

const secretKey = JSON.parse(process.env.MASTER_WALLET_SECRET);
const masterKeypair = Keypair.fromSecretKey(Uint8Array.from(secretKey));
const mintAddress = new PublicKey(process.env.LOYALTY_TOKEN_MINT);
const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

async function transferToken() {
    try {
        const userTokenAccount = await getOrCreateAssociatedTokenAccount(
            connection,
            masterKeypair,
            mintAddress,
            new PublicKey(userWallet)
        );

        const masterTokenAccount = await getOrCreateAssociatedTokenAccount(
            connection,
            masterKeypair,
            mintAddress,
            masterKeypair.publicKey
        );

        await transfer(
            connection,
            masterKeypair,
            masterTokenAccount.address,
            userTokenAccount.address,
            masterKeypair,
            1
        );

        console.log(JSON.stringify({ success: true }));
    } catch (err) {
        console.log(JSON.stringify({ success: false, error: err.message }));
    }
}

transferToken();
